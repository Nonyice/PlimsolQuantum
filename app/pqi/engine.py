from __future__ import annotations

import asyncio
import threading
import traceback
from datetime import datetime, timedelta
from types import SimpleNamespace

from app.enums.market_type import MarketType
from app.intelligence.decision_engine import DecisionEngine
from app.intelligence.indicator_service import IndicatorService
from app.intelligence.market_personality_engine import MarketPersonalityEngine
from app.intelligence.momentum_engine import MomentumEngine
from app.intelligence.opportunity_engine import OpportunityEngine
from app.intelligence.risk_guardian import RiskGuardian
from app.intelligence.support_resistance_engine import SupportResistanceEngine
from app.intelligence.trend_engine import TrendEngine
from app.intelligence.volatility_engine import VolatilityEngine
from app.intelligence.volume_engine import VolumeEngine
from app.models.market_snapshot import MarketSnapshot, TimeframeData
from app.models.pqi_session import PQISession
from app.models.pqi_session_pair import PQISessionPair
from app.pqi import utc_now
from app.pqi.state import PQIState
from app.services.public_market_service import PublicMarketService


class PQIEngine:
    """Persistent PQI runtime shared by trial and live execution.

    Diagnostic build: keeps the persistent-session behaviour, but exposes the
    exact stage at which a scan stops and guarantees that confidence is updated
    when opportunity analysis completes.
    """

    MAX_PAIRS = 3
    ANALYSIS_TIMEFRAMES = ("1m", "5m", "15m", "1h", "4h")
    CHART_TIMEFRAMES = ("5m", "15m", "1h", "4h", "1d")
    MARKET_TIMEOUT = 30
    ANALYSIS_TIMEOUT = 30

    def __init__(self, state=None):
        self._state = state or PQIState()
        self._thread = None
        self._stop_event = threading.Event()
        self._lock = threading.RLock()
        self._app = None
        self._user_id = None
        self._session_id = None
        self._mode = "trial"
        self._live_account = None
        self._components = (
            IndicatorService(), TrendEngine(), MomentumEngine(), VolumeEngine(),
            VolatilityEngine(), SupportResistanceEngine(), MarketPersonalityEngine(),
            OpportunityEngine(),
        )
        self._decision_engine = DecisionEngine()
        self._risk_guardian = RiskGuardian()

    def snapshot(self):
        return self._state

    def _diag(self, message):
        """Print a clear engine diagnostic line to the Flask terminal."""
        stamp = datetime.now().strftime("%H:%M:%S")
        line = f"[PQI {stamp}] {message}"
        print(line, flush=True)
        try:
            self._state.activity.insert(0, {"time": utc_now().isoformat(), "message": message})
            self._state.activity = self._state.activity[:50]
        except Exception:
            pass

    def _set_phase(self, task, decision=None):
        self._state.current_task = task
        if decision is not None:
            self._state.current_decision = decision
        self._diag(f"{task}" + (f" | decision={decision}" if decision else ""))

    def restore_user_session(self, user_id, app=None, session_id=None):
        """Restore a specific ACTIVE session, or the user's latest ACTIVE session."""
        if user_id is None:
            return self._state
        with self._lock:
            self._user_id = user_id
            if app is not None:
                self._app = app
            active = None
            if session_id:
                active = (
                    PQISession.query
                    .filter_by(id=session_id, user_id=user_id, status="ACTIVE")
                    .first()
                )
            if active is None:
                active = (
                    PQISession.query
                    .filter_by(user_id=user_id, status="ACTIVE")
                    .order_by(PQISession.started_at.desc())
                    .first()
                )
            if not active:
                return self._state

            self._session_id = active.id
            self._mode = active.mode
            self._state.session_id = str(active.id)
            self._state.mode = active.mode
            self._state.exchange = active.exchange
            self._state.exchange_id = active.exchange_id or "trial"
            self._state.market_type = active.market_type
            self._state.trading_capital = float(active.capital)
            self._state.starting_capital = float(active.capital)
            self._state.status = "ACTIVE"
            self._state.current_task = "Resuming PQI Session"
            self._state.current_decision = "RESUMING"
            self._load_pairs(active)
            self._revalue_portfolio()
            self._stop_event.clear()
            self._start_worker()
        return self._state

    def configure(self, exchange="binance", market="BTC/USDT", market_type="spot", capital=None):
        self._state.exchange = (exchange or "binance").lower()
        self._state.market = self._normalise_symbol(market)
        self._state.market_type = (market_type or "spot").lower()
        self._state.symbol = self._state.market.replace("/", "")
        if capital is not None:
            capital = float(capital)
            if capital < 10:
                raise ValueError("Minimum trading capital is $10.")
            self._state.trading_capital = capital
            self._state.starting_capital = capital
            self._state.available_capital = capital
            if self._state.status in ("IDLE", "STOPPED", "ERROR"):
                self._state.portfolio_value = capital
        return self._state

    def engage(self, exchange, market, exchange_id="", market_type="spot", live_account=None, capital=None, user_id=None, app=None, new_session=False):
        with self._lock:
            self._user_id = user_id or self._user_id
            self._app = app or self._app
            self._mode = "live" if live_account is not None else "trial"
            self._live_account = live_account
            self.configure(exchange, market, market_type, capital)

            if self._user_id is None:
                raise ValueError("Authenticated user is required for a persistent PQI session.")

            session_obj = None
            if not new_session and self._session_id:
                session_obj = PQISession.query.get(self._session_id)

            if not new_session and (not session_obj or session_obj.status != "ACTIVE"):
                session_obj = (
                    PQISession.query
                    .filter_by(user_id=self._user_id, status="ACTIVE", mode=self._mode)
                    .order_by(PQISession.started_at.desc())
                    .first()
                )

            if not session_obj:
                session_obj = PQISession(
                    user_id=self._user_id,
                    mode=self._mode,
                    exchange=self._state.exchange,
                    exchange_id=exchange_id or "trial",
                    market_type=self._state.market_type,
                    capital=self._state.trading_capital,
                    status="ACTIVE",
                )
                from app.extensions import db
                db.session.add(session_obj)
                db.session.flush()
            else:
                session_obj.exchange = self._state.exchange
                session_obj.exchange_id = exchange_id or session_obj.exchange_id or "trial"
                session_obj.market_type = self._state.market_type
                session_obj.capital = self._state.trading_capital
                session_obj.last_heartbeat = datetime.utcnow()

            self._session_id = session_obj.id
            self._state.session_id = str(session_obj.id)
            self._load_pairs(session_obj)
            self._ensure_pair(session_obj, self._state.market)
            self._load_pairs(session_obj)
            self._revalue_portfolio()

            from app.extensions import db
            db.session.commit()

            self._state.mode = self._mode
            self._state.status = "ACTIVE"
            self._state.exchange_id = exchange_id or "trial"
            self._state.current_decision = "SCANNING"
            self._state.current_task = "Observing Market"
            self._state.connection_status = "CONNECTING"
            self._state.market_status = "STARTING"
            self._state.next_scan = utc_now() + timedelta(seconds=1)
            self._state.activity.insert(0, {"time": utc_now().isoformat(), "message": f"PQI {self._mode.upper()} session {self._session_id} engaged."})
            self._state.activity = self._state.activity[:50]
            self._stop_event.clear()
            self._start_worker()
        return self._state

    def add_pair(self, market):
        if not self._session_id:
            raise ValueError("No active PQI session.")
        session_obj = PQISession.query.get(self._session_id)
        if not session_obj or session_obj.status != "ACTIVE":
            raise ValueError("PQI session is not active.")
        pair = self._ensure_pair(session_obj, self._normalise_symbol(market))
        from app.extensions import db
        db.session.commit()
        self._load_pairs(session_obj)
        return pair

    def pause(self):
        self._state.status = "PAUSED"
        self._state.current_task = "Paused"
        self._state.current_decision = "WAITING"
        return self._state

    def stop(self):
        self._stop_event.set()
        self._state.status = "STOPPED"
        self._state.current_task = "Stopped"
        self._state.current_decision = "IDLE"
        self._state.next_scan = None
        self._state.market_status = "OFFLINE"
        if self._session_id:
            session_obj = PQISession.query.get(self._session_id)
            if session_obj:
                session_obj.status = "STOPPED"
                session_obj.stopped_at = datetime.utcnow()
                session_obj.last_heartbeat = datetime.utcnow()
                from app.extensions import db
                db.session.commit()
        return self._state

    def _start_worker(self):
        if self._thread and self._thread.is_alive():
            self._diag("Worker already running")
            return
        self._thread = threading.Thread(target=self._run_thread, daemon=True, name="pqi-engine")
        self._thread.start()
        self._diag(f"Worker started: {self._thread.name}")

    def _run_thread(self):
        try:
            if self._app is not None:
                with self._app.app_context():
                    asyncio.run(self._run())
            else:
                asyncio.run(self._run())
        except Exception as exc:
            self._engine_error(exc, "worker")

    def _pair_error(self, symbol, exc, stage="scan"):
        """Record an isolated pair failure without killing the whole session."""
        message = f"{stage}: {type(exc).__name__}: {exc}"
        print(f"[PQI PAIR ERROR] {symbol}: {message}", flush=True)
        try:
            self._state.activity.insert(0, {
                "time": utc_now().isoformat(),
                "message": f"{symbol}: {message}",
            })
            self._state.activity = self._state.activity[:50]
            pair = next((p for p in self._state.session_pairs if p.get("symbol") == symbol), None)
            if pair:
                pair["last_update"] = utc_now().isoformat()
                self._persist_pair(symbol)
                from app.extensions import db
                db.session.commit()
        except Exception:
            pass

    def _engine_error(self, exc, stage="unknown"):
        message = f"{stage}: {type(exc).__name__}: {exc}"
        print("[PQI ERROR] " + message, flush=True)
        traceback.print_exc()
        self._state.status = "ERROR"
        self._state.current_task = f"Engine Error ({stage})"
        self._state.current_decision = message
        self._state.connection_status = "ERROR"
        self._state.market_status = "ERROR"
        try:
            self._state.activity.insert(0, {"time": utc_now().isoformat(), "message": "ERROR: " + message})
            self._state.activity = self._state.activity[:50]
        except Exception:
            pass

    async def _run(self):
        self._diag(f"Runtime entered mode={self._mode}")
        if self._mode == "live":
            await self._run_live()
        else:
            await self._run_trial()

    async def _run_trial(self):
        try:
            self._set_phase("Loading Live Trial Market", "SCANNING")
            self._diag(f"Market request: exchange={self._state.exchange}, type={self._state.market_type}")

            # The configured session pairs are the source of truth for the
            # trading runtime.  Full exchange market discovery is useful for
            # the selector, but it must never prevent an already configured
            # pair from being analysed/traded.
            markets = []
            try:
                markets = await asyncio.wait_for(
                    PublicMarketService.markets(self._state.exchange, self._state.market_type),
                    timeout=self.MARKET_TIMEOUT,
                )
                self._state.markets = markets[:1000]
                self._diag(f"Market list loaded: {len(markets)} symbols")
            except (asyncio.TimeoutError, Exception) as exc:
                self._state.markets = list(getattr(self._state, "markets", []) or [])
                self._diag(f"Market discovery unavailable ({type(exc).__name__}); continuing with configured session pairs")

            session_obj = PQISession.query.get(self._session_id)
            if not session_obj:
                raise RuntimeError("Persistent PQI session could not be restored.")
            self._load_pairs(session_obj)
            configured_symbols = {p["symbol"] for p in self._state.session_pairs}
            if markets:
                for pair in list(self._state.session_pairs):
                    # Do not destroy a persisted position/watchlist record just
                    # because the optional catalogue request was incomplete.
                    if pair["symbol"] not in markets and pair.get("status") != "OPEN":
                        self._diag(f"Configured pair not present in catalogue: {pair['symbol']} (will still be scanned)")
            if not configured_symbols:
                raise RuntimeError("No configured trading pair is available for this session.")

            self._state.exchange_connected = True
            self._state.connection_status = "CONNECTED"
            self._state.market_status = "ONLINE"
            self._state.mode = "trial"
            if self._state.trading_capital < 10:
                raise ValueError("Select trial capital of at least $10 before engaging PQI.")

            if not self._state.equity_curve:
                self._state.portfolio_value = self._state.trading_capital
                self._state.available_capital = self._state.trading_capital
                self._state.starting_capital = self._state.trading_capital

            self._diag("Trial runtime ONLINE; entering scan loop")
            while not self._stop_event.is_set():
                if self._state.status == "PAUSED":
                    await asyncio.sleep(1)
                    continue
                if self._state.status != "ACTIVE":
                    break
                await self._scan_all_trial_pairs()
                session_obj.last_heartbeat = datetime.utcnow()
                from app.extensions import db
                db.session.commit()
                await asyncio.sleep(5)
        except Exception as exc:
            self._engine_error(exc, "trial-runtime")

    async def _scan_all_trial_pairs(self):
        # Keep one live/watchlist record per symbol. Closed trade records are
        # retained for realised-profit accounting, but the latest record for
        # that symbol remains eligible for a fresh market scan.
        latest_by_symbol = {}
        for p in self._state.session_pairs:
            if p.get("status") == "UNAVAILABLE":
                continue
            latest_by_symbol[p["symbol"]] = p
        pairs = list(latest_by_symbol.values())[: self.MAX_PAIRS]
        if not pairs:
            raise RuntimeError("No available trading pair is configured for this session.")
        self._set_phase(f"Scanning {len(pairs)} pair(s)", "SCANNING")
        for pair in pairs:
            await self._scan_public_pair(pair["symbol"])
        self._state.open_positions = sum(1 for p in self._state.session_pairs if p.get("status") == "OPEN")
        self._state.available_capital = self._state.portfolio_value

    async def _scan_public_pair(self, symbol):
        try:
            self._set_phase(f"Fetching market data: {symbol}", "SCANNING")
            requested = list(self.ANALYSIS_TIMEFRAMES)
            candle_results = await asyncio.wait_for(
                asyncio.gather(*[
                    PublicMarketService.candles(self._state.exchange, self._state.market_type, symbol, tf, 220)
                    for tf in requested
                ]),
                timeout=self.MARKET_TIMEOUT,
            )
            self._diag(f"Candles received for {symbol}: " + ", ".join(f"{tf}={len(data or [])}" for tf, data in zip(requested, candle_results)))

            self._set_phase(f"Fetching ticker: {symbol}", "CONNECTING")
            ticker = await asyncio.wait_for(
                PublicMarketService.ticker(self._state.exchange, self._state.market_type, symbol),
                timeout=self.MARKET_TIMEOUT,
            )
            candles_by_tf = {tf: data for tf, data in zip(requested, candle_results)}
            h1 = candles_by_tf.get("1h") or []
            if not h1:
                raise RuntimeError(f"No 1h candle data returned for {symbol}.")

            self._state.last_price = float(ticker.get("last") or h1[-1][4])
            self._state.bid = ticker.get("bid")
            self._state.ask = ticker.get("ask")
            self._state.spread = (self._state.ask - self._state.bid) if self._state.ask and self._state.bid else None
            self._state.volume_24h = ticker.get("volume")
            self._state.high_24h = ticker.get("high")
            self._state.low_24h = ticker.get("low")
            self._state.change_percent_24h = ticker.get("percentage")
            self._state.last_market_update = utc_now()
            self._state.candles = self._format_candles(h1[-120:])
            self._state.candles_by_timeframe = {tf: self._format_candles(c[-120:]) for tf, c in candles_by_tf.items() if c}

            self._set_phase(f"Calculating intelligence: {symbol}", "CALCULATING")
            # Pass the current position side into intelligence so SPOT can
            # execute a bearish SELL as a close of an existing LONG instead of
            # incorrectly treating every SELL as an attempt to open a short.
            existing_pair = next(
                (p for p in reversed(self._state.session_pairs)
                 if p.get("symbol") == symbol and p.get("status") == "OPEN"),
                None,
            )
            existing_side = existing_pair.get("side") if existing_pair else None

            analysis = await asyncio.wait_for(
                asyncio.to_thread(
                    self._analyse_mtf,
                    candles_by_tf,
                    symbol,
                    self._state.exchange,
                    self._state.market_type,
                    self._state.last_price,
                    existing_side,
                ),
                timeout=self.ANALYSIS_TIMEOUT,
            )
            self._diag(f"Analysis completed: {symbol}")
            self._apply_analysis(analysis, symbol)
            decision = analysis["decision"]
            self._diag(
                f"DECISION {symbol}: action={getattr(decision, 'action', None)} "
                f"execute={getattr(decision, 'should_execute', None)} "
                f"confidence={getattr(decision, 'confidence', None)}"
            )
            self._simulate_paper(analysis, symbol)
            self._persist_pair(symbol)
            self._diag(f"Scan completed: {symbol} | confidence={self._state.confidence}")
        except asyncio.TimeoutError:
            self._pair_error(symbol, RuntimeError(f"Timeout while processing {symbol}"), "timeout")
        except Exception as exc:
            self._pair_error(symbol, exc, "scan")

    def _analyse_mtf(self, candles_by_tf, symbol, exchange, market_type, ticker_last=None, existing_side=None):
        self._diag(f"ANALYSIS START {symbol}: indicators")
        indicator_service, trend, momentum, volume, volatility, support, personality, opportunity = self._components
        snapshot = MarketSnapshot(symbol=symbol.replace("/", ""), exchange=exchange)
        for tf, candles in candles_by_tf.items():
            if candles:
                snapshot.timeframes[tf] = TimeframeData(tf, candles, indicator_service.calculate(candles))
        if not snapshot.timeframes:
            raise RuntimeError(f"No valid timeframe data available for {symbol}.")
        snapshot.ticker = {"lastPrice": float(ticker_last or (candles_by_tf.get("1m") or candles_by_tf.get("5m") or candles_by_tf.get("1h") or list(candles_by_tf.values())[0])[-1][4])}

        self._diag(f"ANALYSIS {symbol}: trend")
        trend_a = trend.analyse(snapshot)
        self._diag(f"ANALYSIS {symbol}: momentum")
        momentum_a = momentum.analyse(snapshot)
        self._diag(f"ANALYSIS {symbol}: volume")
        volume_a = volume.analyse(snapshot)
        self._diag(f"ANALYSIS {symbol}: volatility")
        volatility_a = volatility.analyse(snapshot)
        self._diag(f"ANALYSIS {symbol}: support/resistance")
        support_a = support.analyse(snapshot)
        self._diag(f"ANALYSIS {symbol}: personality")
        personality_a = personality.analyse(trend_a, momentum_a, volume_a, volatility_a, support_a)
        self._diag(f"ANALYSIS {symbol}: opportunity")
        opportunity_a = opportunity.evaluate(trend_a, momentum_a, volume_a, volatility_a, support_a, personality_a, snapshot=snapshot)
        self._diag(f"ANALYSIS {symbol}: opportunity score={getattr(opportunity_a, 'score', None)} probability={getattr(opportunity_a, 'probability', None)}")
        # The intelligence/risk layers expect a trading-account-like object.
        # Trial mode does not have a TradingAccount row, so provide the
        # persistent PQI session id as a stable synthetic account id.
        trial_account = SimpleNamespace(
            id=self._session_id,
            market_type=MarketType(market_type),
            exchange=SimpleNamespace(value=exchange),
        )
        self._diag(f"ANALYSIS {symbol}: decision")
        decision = self._decision_engine.decide(
            opportunity_a,
            trend_a,
            momentum_a,
            volatility_a,
            personality_a,
            trial_account,
            existing_position=existing_side,
        )
        self._diag(f"ANALYSIS COMPLETE {symbol}: action={getattr(decision, 'action', None)} execute={getattr(decision, 'should_execute', None)} confidence={getattr(decision, 'confidence', None)}")
        return locals()

    def _apply_analysis(self, a, symbol):
        opportunity = a["opportunity_a"]
        decision = a["decision"]
        probability = getattr(opportunity, "probability", None)
        decision_confidence = getattr(decision, "confidence", None)
        if probability is not None:
            self._state.confidence = float(probability)
        elif decision_confidence is not None:
            self._state.confidence = float(decision_confidence)
        else:
            raise RuntimeError(f"Confidence was not produced by analysis for {symbol}.")

        self._state.signals_analysed += 1
        self._state.market_regime = a["personality_a"].personality
        self._state.current_decision = decision.action if decision.should_execute else "WAIT"
        self._state.current_task = "Analysis Complete"
        self._state.intelligence = {
            "trend": a["trend_a"].overall_direction,
            "momentum": a["momentum_a"].overall_direction,
            "volume": a["volume_a"].overall_direction,
            "volatility": a["volatility_a"].overall_regime,
            "personality": a["personality_a"].personality,
            "opportunity_score": opportunity.score,
            "probability": opportunity.probability,
            "confidence": self._state.confidence,
            "reason": opportunity.reason,
            "signal": decision.action,
            "entry": self._state.last_price,
            "timeframe": "1h anchor / 15m + 4h confirmation",
            "symbol": symbol,
        }
        self._diag(f"CONFIDENCE UPDATED {symbol}: {self._state.confidence}")
        self._state.activity.insert(0, {"time": utc_now().isoformat(), "message": f"{symbol}: {self._state.current_decision} · confidence {self._state.confidence:.2f} · {opportunity.reason}"})
        self._state.activity = self._state.activity[:50]
        self._state.next_scan = utc_now() + timedelta(seconds=8)

    def _simulate_paper(self, a, symbol):
        """Run the trial portfolio as a continuous compounding account.

        Realised PnL is never put back to zero when a position closes. Closed
        trade rows are retained and a new row is created for the next trade,
        so every profitable trade remains part of the account equity.
        """
        price = float(self._state.last_price or 0)
        if price <= 0 or self._state.trading_capital < 10:
            return

        # The latest record is the active/watchlist record for this symbol.
        pair = None
        for candidate in reversed(self._state.session_pairs):
            if candidate.get("symbol") == symbol:
                pair = candidate
                break
        if not pair:
            return

        if pair.get("status") == "OPEN":
            side = pair["side"]
            entry = float(pair["entry_price"] or 0)
            if entry <= 0:
                return

            pnl_pct = (
                (price - entry) / entry
                if side == "LONG"
                else (entry - price) / entry
            )
            pair["mark_price"] = price
            pair["pnl"] = float(pair["notional"] or 0) * pnl_pct
            profit_pct = pnl_pct * 100.0

            # SL/TP are established at entry by RiskGuardian. Once the trade
            # moves in PQI's favour, ratchet the SL forward only; never move
            # a protective stop backwards. This preserves realised profit while
            # still allowing the position to run toward its original TP.
            if profit_pct >= 0.30:
                if side == "LONG":
                    breakeven_stop = entry * 1.0010
                    trailing_stop = price * 0.9970
                    pair["stop_loss"] = max(
                        float(pair["stop_loss"] or 0),
                        breakeven_stop,
                        trailing_stop,
                    )
                else:
                    breakeven_stop = entry * 0.9990
                    trailing_stop = price * 1.0030
                    current_stop = float(pair["stop_loss"] or 0)
                    pair["stop_loss"] = min(
                        current_stop if current_stop > 0 else trailing_stop,
                        breakeven_stop,
                        trailing_stop,
                    )

            # TP closes a favourable cycle. SL closes an invalidated cycle.
            # A sufficiently confident opposite decision can also close the
            # current position. On SPOT this is the correct SELL behaviour:
            # SELL disposes of the LONG asset already owned by PQI; it does not
            # create a naked SHORT. The next scan may then open a fresh cycle.
            decision = a["decision"]
            closed = False
            if (side == "LONG" and price >= float(pair["take_profit"])) or (
                side == "SHORT" and price <= float(pair["take_profit"])
            ):
                self._close_pair(pair, "TAKE PROFIT")
                closed = True
            elif (side == "LONG" and price <= float(pair["stop_loss"])) or (
                side == "SHORT" and price >= float(pair["stop_loss"])
            ):
                self._close_pair(pair, "STOP LOSS")
                closed = True
            elif (
                decision.should_execute
                and float(getattr(decision, "confidence", 0) or 0) >= 60.1
                and ((side == "LONG" and decision.action == "SELL")
                     or (side == "SHORT" and decision.action == "BUY"))
            ):
                self._close_pair(pair, f"SIGNAL REVERSAL ({decision.action})")
                closed = True

        else:
            decision = a["decision"]
            if decision.should_execute and decision.action in ("BUY", "SELL"):
                # Closed trades remain historical. Create a fresh trade row so
                # their realised PnL can never be overwritten by the next entry.
                if pair.get("status") == "CLOSED":
                    session_obj = PQISession.query.get(self._session_id)
                    new_db_pair = self._ensure_pair(session_obj, symbol)
                    pair = {
                        "id": str(new_db_pair.id), "symbol": symbol, "status": "OBSERVING",
                        "side": None, "entry_price": None, "mark_price": None,
                        "quantity": None, "notional": None, "stop_loss": None,
                        "take_profit": None, "pnl": 0.0, "opened_at": None,
                        "closed_at": None, "last_update": utc_now().isoformat(),
                    }
                    self._state.session_pairs.append(pair)

                realised = self._realised_pnl()
                floating = self._floating_pnl()
                equity = self._state.trading_capital + realised + floating
                risk_account = SimpleNamespace(
                    id=self._session_id,
                    market_type=MarketType(self._state.market_type),
                    exchange=SimpleNamespace(value=self._state.exchange),
                )
                risk = self._risk_guardian.evaluate(
                    risk_account,
                    decision,
                    a["snapshot"],
                    max(equity, 0.0),
                )
                if not risk.get("approved"):
                    self._diag(
                        f"RISK REJECT {symbol}: "
                        f"{risk.get('reason', 'risk guardian rejected entry')}"
                    )
                if risk.get("approved"):
                    used = sum(float(p.get("notional") or 0) for p in self._state.session_pairs if p.get("status") == "OPEN")
                    available = max(0.0, equity - used)

                    # CA is the fixed capital allocation for each trade.
                    # Realised profit/loss stays in account equity, but it is
                    # not silently compounded into the next trade's allocation.
                    # This returns the original CA to the trading cycle after
                    # every close while preserving realised P/L separately.
                    trade_ca = max(10.0, float(self._state.trading_capital))
                    notional = min(available, trade_ca)
                    if notional >= 10:
                        side = "LONG" if decision.action == "BUY" else "SHORT"
                        pair.update({
                            "status": "OPEN", "side": side, "quantity": notional / price,
                            "notional": notional, "entry_price": price, "mark_price": price,
                            "stop_loss": risk["stop_loss"], "take_profit": risk["take_profit"],
                            "pnl": 0.0, "opened_at": utc_now().isoformat(), "closed_at": None,
                        })
                        self._state.trades_today += 1
                        self._state.execution_log.insert(0, {
                            "time": utc_now().isoformat(), "symbol": symbol,
                            "side": decision.action, "status": "PAPER OPEN",
                            "session_id": self._state.session_id,
                            "equity_before_entry": round(equity, 8),
                            "realised_pnl": round(realised, 8),
                        })
                        self._state.execution_log = self._state.execution_log[:50]

        self._revalue_portfolio()
        self._state.equity_curve.append({"time": utc_now().isoformat(), "value": round(self._state.portfolio_value, 4)})
        self._state.equity_curve = self._state.equity_curve[-180:]
        self._persist_pair(symbol)

    def _close_pair(self, pair, reason):
        """Close a trial position and retain its realised result.

        A close is the end of the current market cycle, not the end of the
        session. The next scan can create a fresh pair record and re-enter
        when the current decision again authorises BUY or SELL.
        """
        if pair.get("status") != "OPEN":
            return

        pair["status"] = "CLOSED"
        pair["closed_at"] = utc_now().isoformat()
        pair["mark_price"] = float(self._state.last_price or pair.get("mark_price") or 0)
        pair["last_update"] = pair["closed_at"]

        self._state.execution_log.insert(0, {
            "time": pair["closed_at"],
            "symbol": pair.get("symbol"),
            "side": "BUY" if pair.get("side") == "LONG" else "SELL",
            "status": "PAPER CLOSE",
            "reason": reason,
            "pnl": round(float(pair.get("pnl") or 0), 8),
            "session_id": self._state.session_id,
        })
        self._state.execution_log = self._state.execution_log[:50]
        self._diag(
            f"TRIAL POSITION CLOSED {pair.get('symbol')}: "
            f"{reason} | pnl={float(pair.get('pnl') or 0):.8f}"
        )

    def _realised_pnl(self):
        return round(sum(float(p.get("pnl") or 0) for p in self._state.session_pairs if p.get("status") == "CLOSED"), 8)

    def _floating_pnl(self):
        return round(sum(float(p.get("pnl") or 0) for p in self._state.session_pairs if p.get("status") == "OPEN"), 8)

    def _revalue_portfolio(self):
        realised = self._realised_pnl()
        floating = self._floating_pnl()
        equity = max(0.0, self._state.trading_capital + realised + floating)
        used = sum(float(p.get("notional") or 0) for p in self._state.session_pairs if p.get("status") == "OPEN")
        self._state.daily_pnl = realised + floating
        self._state.portfolio_value = equity
        self._state.available_capital = max(0.0, equity - used)
        self._state.open_positions = sum(1 for p in self._state.session_pairs if p.get("status") == "OPEN")
        self._state.realised_pnl = realised
        self._state.unrealised_pnl = floating
        self._state.win_rate = self._calculate_win_rate()

    def _calculate_win_rate(self):
        closed = [p for p in self._state.session_pairs if p.get("status") == "CLOSED"]
        if not closed:
            return 0.0
        wins = sum(1 for p in closed if float(p.get("pnl") or 0) > 0)
        return round((wins / len(closed)) * 100.0, 2)

    def _ensure_pair(self, session_obj, market):
        symbol = self._normalise_symbol(market).replace("/", "")
        existing = next((p for p in session_obj.pairs if p.symbol == symbol and p.status != "CLOSED"), None)
        if existing:
            return existing
        active = [p for p in session_obj.pairs if p.status in ("OBSERVING", "OPEN")]
        if len(active) >= self.MAX_PAIRS:
            raise ValueError("A PQI session can monitor a maximum of 3 pairs.")
        pair = PQISessionPair(
            session_id=session_obj.id,
            symbol=symbol,
            status="OBSERVING",
            last_update=datetime.utcnow(),
        )
        from app.extensions import db
        db.session.add(pair)
        db.session.flush()
        return pair

    def _load_pairs(self, session_obj):
        self._state.session_pairs = []
        for p in session_obj.pairs:
            self._state.session_pairs.append({
                "id": str(p.id), "symbol": p.symbol, "status": p.status, "side": p.side,
                "entry_price": float(p.entry_price) if p.entry_price is not None else None,
                "mark_price": float(p.mark_price) if p.mark_price is not None else None,
                "quantity": float(p.quantity) if p.quantity is not None else None,
                "notional": float(p.notional) if p.notional is not None else None,
                "stop_loss": float(p.stop_loss) if p.stop_loss is not None else None,
                "take_profit": float(p.take_profit) if p.take_profit is not None else None,
                "pnl": float(p.pnl or 0), "opened_at": p.opened_at.isoformat() if p.opened_at else None,
                "closed_at": p.closed_at.isoformat() if p.closed_at else None,
                "last_update": p.last_update.isoformat() if p.last_update else None,
            })
        self._state.open_positions = sum(1 for p in self._state.session_pairs if p.get("status") == "OPEN")

    def _persist_pair(self, symbol):
        if not self._session_id:
            return
        session_obj = PQISession.query.get(self._session_id)
        if not session_obj:
            return
        state_pair = next((p for p in reversed(self._state.session_pairs) if p["symbol"] == symbol and p.get("status") != "CLOSED"), None) or next((p for p in reversed(self._state.session_pairs) if p["symbol"] == symbol), None)
        db_pair = next((p for p in session_obj.pairs if p.symbol == symbol and str(p.id) == state_pair["id"]), None) if state_pair else None
        if not db_pair or not state_pair:
            return
        db_pair.status = state_pair["status"]
        db_pair.side = state_pair.get("side")
        for field in ("entry_price", "mark_price", "quantity", "notional", "stop_loss", "take_profit", "pnl"):
            setattr(db_pair, field, state_pair.get(field))
        db_pair.last_update = datetime.utcnow()
        if state_pair.get("opened_at") and not db_pair.opened_at:
            db_pair.opened_at = datetime.fromisoformat(state_pair["opened_at"].replace("Z", "+00:00")).replace(tzinfo=None)
        if state_pair.get("closed_at"):
            db_pair.closed_at = datetime.utcnow()

    async def _run_live(self):
        from app.trading.trading_service import TradingService
        account = self._live_account
        self._state.exchange_connected = True
        self._state.connection_status = "CONNECTED"
        self._state.market_status = "ONLINE"
        self._state.mode = "live"
        service = TradingService()
        self._diag("Live runtime ONLINE")
        while not self._stop_event.is_set():
            if self._state.status == "PAUSED":
                await asyncio.sleep(1)
                continue
            if self._state.status != "ACTIVE":
                break
            try:
                self._set_phase("Live Trading Cycle", "SCANNING")
                if not getattr(account, "can_trade", False):
                    # Live dashboard can run the same PQI intelligence pipeline
                    # against the connected exchange without placing orders until
                    # the account is explicitly authorized for trading.
                    self._diag("LIVE account connected; trade authorization is OFF")
                    credentials = account.get_credentials()
                    exchange_adapter = __import__("app.trading.exchanges.factory", fromlist=["ExchangeFactory"]).ExchangeFactory.create(
                        exchange=account.exchange,
                        market_type=account.market_type,
                        api_key=credentials["api_key"],
                        api_secret=credentials["api_secret"],
                        testnet=account.is_testnet,
                    )
                    balances = await exchange_adapter.get_account_balance()
                    account_balance = service._get_balance(balances, account.market_type)
                    snapshot = await service.pqi.observe(account, symbol=self._state.symbol)
                    analysis = await service.pqi.analyse(snapshot=snapshot, trading_account=account, account_balance=min(account_balance, self._state.trading_capital))
                else:
                    result = await asyncio.wait_for(
                        service.run(account, capital=self._state.trading_capital, symbol=self._state.symbol),
                        timeout=self.MARKET_TIMEOUT,
                    )
                    analysis = result.get("analysis") or {}
                snapshot = analysis.get("snapshot")
                if snapshot:
                    self._state.last_price = float((snapshot.ticker or {}).get("lastPrice", 0))
                    tf = snapshot.timeframes.get("1h")
                    if tf:
                        self._state.candles = self._format_candles(tf.candles[-120:])
                decision = analysis.get("decision")
                opportunity = analysis.get("opportunity")
                if opportunity is not None and getattr(opportunity, "probability", None) is not None:
                    self._state.confidence = float(opportunity.probability)
                elif decision:
                    confidence = getattr(decision, "confidence", None)
                    if confidence is not None:
                        self._state.confidence = float(confidence)
                if decision:
                    self._state.current_decision = decision.action if decision.should_execute else "WAIT"
                    self._diag(f"LIVE CONFIDENCE UPDATED: {self._state.confidence}")
                else:
                    self._diag("LIVE cycle returned no decision")
                self._state.current_task = "Live Trading Cycle Complete"
                self._state.signals_analysed += 1
                self._state.next_scan = utc_now() + timedelta(seconds=8)
                if self._session_id:
                    s = PQISession.query.get(self._session_id)
                    if s:
                        s.last_heartbeat = datetime.utcnow()
                        from app.extensions import db
                        db.session.commit()
            except Exception as exc:
                self._engine_error(exc, "live-cycle")
                if self._state.status == "ERROR":
                    break
            await asyncio.sleep(8)

    @staticmethod
    def _format_candles(candles):
        return [{"time": int(c[0]), "open": float(c[1]), "high": float(c[2]), "low": float(c[3]), "close": float(c[4]), "volume": float(c[5])} for c in candles]

    @staticmethod
    def _normalise_symbol(symbol):
        symbol = (symbol or "BTCUSDT").upper().strip()
        if "/" in symbol:
            return symbol
        if symbol.endswith("USDT"):
            return symbol[:-4] + "/USDT"
        return symbol


engine = PQIEngine()
