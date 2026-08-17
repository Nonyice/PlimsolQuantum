from __future__ import annotations

import asyncio
import threading
from datetime import timedelta
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
from app.pqi import pqi_state, utc_now
from app.services.public_market_service import PublicMarketService


class PQIEngine:
    """Runs the same market/intelligence pipeline in trial and live modes."""

    def __init__(self):
        self._thread = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
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
        now = utc_now()
        if pqi_state.status == "ACTIVE" and pqi_state.next_scan and now >= pqi_state.next_scan:
            pqi_state.next_scan = now + timedelta(seconds=10)
        return pqi_state

    def configure(self, exchange="binance", market="BTC/USDT", market_type="spot", capital=None):
        pqi_state.exchange = (exchange or "binance").lower()
        pqi_state.market = (market or "BTC/USDT").upper().replace("BTCUSDT", "BTC/USDT")
        pqi_state.market_type = (market_type or "spot").lower()
        pqi_state.symbol = pqi_state.market.replace("/", "")
        if capital is not None:
            capital = float(capital)
            if capital < 10:
                raise ValueError("Minimum trading capital is $10.")
            pqi_state.trading_capital = capital
            pqi_state.starting_capital = capital
            pqi_state.available_capital = capital
            if pqi_state.status in ("IDLE", "STOPPED", "ERROR"):
                pqi_state.portfolio_value = capital
        return pqi_state

    def engage(self, exchange, market, exchange_id="", market_type="spot", live_account=None, capital=None):
        with self._lock:
            self._mode = "live" if live_account is not None else "trial"
            self._live_account = live_account
            self.configure(exchange, market, market_type, capital)

            if self._thread and self._thread.is_alive():
                pqi_state.status = "ACTIVE"
                return pqi_state

            pqi_state.mode = self._mode
            pqi_state.status = "ACTIVE"
            pqi_state.exchange_id = exchange_id or "trial"
            pqi_state.current_decision = "SCANNING"
            pqi_state.current_task = "Starting PQI"
            pqi_state.connection_status = "CONNECTING"
            pqi_state.market_status = "STARTING"
            pqi_state.next_scan = utc_now() + timedelta(seconds=1)
            pqi_state.activity.insert(0, {"time": utc_now().isoformat(), "message": f"PQI {self._mode.upper()} engaged."})
            pqi_state.activity = pqi_state.activity[:50]
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._run_thread, daemon=True, name="pqi-engine")
            self._thread.start()
        return pqi_state

    def pause(self):
        pqi_state.status = "PAUSED"
        pqi_state.current_task = "Paused"
        pqi_state.current_decision = "WAITING"
        return pqi_state

    def stop(self):
        self._stop_event.set()
        pqi_state.status = "STOPPED"
        pqi_state.current_task = "Stopped"
        pqi_state.current_decision = "IDLE"
        pqi_state.next_scan = None
        pqi_state.market_status = "OFFLINE"
        return pqi_state

    def _run_thread(self):
        try:
            asyncio.run(self._run())
        except Exception as exc:
            pqi_state.status = "ERROR"
            pqi_state.current_task = "Engine Error"
            pqi_state.current_decision = str(exc)
            pqi_state.connection_status = "ERROR"
            pqi_state.market_status = "ERROR"

    async def _run(self):
        if self._mode == "live":
            await self._run_live()
        else:
            await self._run_trial()

    async def _run_trial(self):
        try:
            pqi_state.current_task = "Loading Live Trial Market"
            markets = await PublicMarketService.markets(pqi_state.exchange, pqi_state.market_type)
            pqi_state.markets = list(markets)
            symbol = self._normalise_symbol(pqi_state.market)
            compact = symbol.replace("/", "")
            if compact not in pqi_state.markets:
                raise ValueError(f"Trading pair {compact} is not available on {pqi_state.exchange} {pqi_state.market_type}.")

            pqi_state.exchange_connected = True
            pqi_state.connection_status = "CONNECTED"
            pqi_state.market_status = "ONLINE"
            pqi_state.mode = "trial"
            if pqi_state.trading_capital < 10:
                raise ValueError("Select trial capital of at least $10 before engaging PQI.")
            if not pqi_state.equity_curve:
                pqi_state.portfolio_value = pqi_state.trading_capital
                pqi_state.available_capital = pqi_state.trading_capital
                pqi_state.starting_capital = pqi_state.trading_capital

            while not self._stop_event.is_set():
                if pqi_state.status == "PAUSED":
                    await asyncio.sleep(1)
                    continue
                if pqi_state.status != "ACTIVE":
                    break
                # Read the current selection every cycle so changing the
                # dashboard pair immediately changes the running engine.
                symbol = self._normalise_symbol(pqi_state.market)
                compact = symbol.replace("/", "")
                if compact not in pqi_state.markets:
                    pqi_state.markets = await PublicMarketService.markets(pqi_state.exchange, pqi_state.market_type)
                if compact not in pqi_state.markets:
                    raise ValueError(f"Trading pair {compact} is not available on {pqi_state.exchange} {pqi_state.market_type}.")
                pqi_state.symbol = compact
                pqi_state.market = symbol
                await self._scan_public(symbol)
                await asyncio.sleep(8)
        except Exception as exc:
            pqi_state.status = "ERROR"
            pqi_state.connection_status = "ERROR"
            pqi_state.market_status = "ERROR"
            pqi_state.current_task = "Market feed unavailable"
            pqi_state.current_decision = str(exc)

    async def _scan_public(self, symbol):
        pqi_state.current_task = "Scanning Live Market"
        ohlcv, ticker = await asyncio.gather(
            PublicMarketService.candles(pqi_state.exchange, pqi_state.market_type, symbol, "1h", 180),
            PublicMarketService.ticker(pqi_state.exchange, pqi_state.market_type, symbol),
        )
        if not ohlcv:
            raise RuntimeError("No candle data returned by exchange.")

        pqi_state.last_price = float(ticker.get("last") or ohlcv[-1][4])
        pqi_state.bid = ticker.get("bid")
        pqi_state.ask = ticker.get("ask")
        pqi_state.spread = (pqi_state.ask - pqi_state.bid) if pqi_state.ask and pqi_state.bid else None
        pqi_state.volume_24h = ticker.get("volume")
        pqi_state.high_24h = ticker.get("high")
        pqi_state.low_24h = ticker.get("low")
        pqi_state.change_percent_24h = ticker.get("percentage")
        pqi_state.last_market_update = utc_now()
        pqi_state.candles = [
            {"time": int(c[0]), "open": float(c[1]), "high": float(c[2]), "low": float(c[3]), "close": float(c[4]), "volume": float(c[5])}
            for c in ohlcv[-120:]
        ]
        analysis = self._analyse(ohlcv, symbol, pqi_state.exchange, pqi_state.market_type)
        self._apply_analysis(analysis)
        self._simulate_paper(analysis)

    def _analyse(self, candles, symbol, exchange, market_type):
        indicator_service, trend, momentum, volume, volatility, support, personality, opportunity = self._components
        snapshot = MarketSnapshot(symbol=symbol.replace("/", ""), exchange=exchange)
        indicators = indicator_service.calculate(candles)
        snapshot.timeframes["1h"] = TimeframeData("1h", candles, indicators)
        snapshot.ticker = {"lastPrice": float(candles[-1][4])}
        trend_a = trend.analyse(snapshot)
        momentum_a = momentum.analyse(snapshot)
        volume_a = volume.analyse(snapshot)
        volatility_a = volatility.analyse(snapshot)
        support_a = support.analyse(snapshot)
        personality_a = personality.analyse(trend_a, momentum_a, volume_a, volatility_a, support_a)
        opportunity_a = opportunity.evaluate(trend_a, momentum_a, volume_a, volatility_a, support_a, personality_a)
        trial_account = SimpleNamespace(market_type=MarketType(pqi_state.market_type), exchange=SimpleNamespace(value=exchange))
        decision = self._decision_engine.decide(opportunity_a, trend_a, momentum_a, volatility_a, personality_a, trial_account)
        return locals()

    def _apply_analysis(self, a):
        opportunity = a["opportunity_a"]
        pqi_state.signals_analysed += 1
        pqi_state.confidence = float(opportunity.probability)
        pqi_state.market_regime = a["personality_a"].personality
        decision = a["decision"]
        pqi_state.current_decision = decision.action if decision.should_execute else "WAIT"
        pqi_state.intelligence = {
            "trend": a["trend_a"].overall_direction,
            "momentum": a["momentum_a"].overall_direction,
            "volume": a["volume_a"].overall_direction,
            "volatility": a["volatility_a"].overall_regime,
            "personality": a["personality_a"].personality,
            "opportunity_score": opportunity.score,
            "probability": opportunity.probability,
            "reason": opportunity.reason,
            "signal": decision.action,
            "entry": pqi_state.last_price,
        }
        pqi_state.activity.insert(0, {"time": utc_now().isoformat(), "message": f"{pqi_state.current_decision}: {opportunity.reason}"})
        pqi_state.activity = pqi_state.activity[:50]
        pqi_state.next_scan = utc_now() + timedelta(seconds=8)

    def _simulate_paper(self, a):
        price = float(pqi_state.last_price or 0)
        if price <= 0 or pqi_state.trading_capital < 10:
            return

        # Manage existing simulated position first.
        position = pqi_state.paper_position
        if position:
            side = position["side"]
            pnl_pct = ((price - position["entry_price"]) / position["entry_price"]) if side == "LONG" else ((position["entry_price"] - price) / position["entry_price"])
            position["mark_price"] = price
            position["pnl"] = position["notional"] * pnl_pct
            pqi_state.portfolio_value = pqi_state.trading_capital + position["pnl"]
            pqi_state.daily_pnl = position["pnl"]
            if price >= position["take_profit"] if side == "LONG" else price <= position["take_profit"]:
                self._close_paper("TAKE PROFIT")
            elif price <= position["stop_loss"] if side == "LONG" else price >= position["stop_loss"]:
                self._close_paper("STOP LOSS")
        else:
            decision = a["decision"]
            if decision.should_execute and decision.action in ("BUY", "SELL"):
                risk = self._risk_guardian.evaluate(
                    SimpleNamespace(market_type=MarketType(pqi_state.market_type)),
                    decision,
                    a["snapshot"],
                    pqi_state.trading_capital,
                )
                if risk.get("approved"):
                    notional = min(pqi_state.trading_capital, pqi_state.trading_capital * max(decision.risk_percent, 1) / 100 * 10)
                    side = "LONG" if decision.action == "BUY" else "SHORT"
                    pqi_state.paper_position = {
                        "symbol": pqi_state.symbol,
                        "side": side,
                        "quantity": notional / price,
                        "notional": notional,
                        "entry_price": price,
                        "mark_price": price,
                        "stop_loss": risk["stop_loss"],
                        "take_profit": risk["take_profit"],
                        "pnl": 0.0,
                        "opened_at": utc_now().isoformat(),
                    }
                    pqi_state.open_positions = 1
                    pqi_state.trades_today += 1
                    pqi_state.execution_log.insert(0, {"time": utc_now().isoformat(), "symbol": pqi_state.symbol, "side": decision.action, "status": "PAPER OPEN"})
                    pqi_state.execution_log = pqi_state.execution_log[:50]

        pqi_state.equity_curve.append({"time": utc_now().isoformat(), "value": round(pqi_state.portfolio_value, 4)})
        pqi_state.equity_curve = pqi_state.equity_curve[-180:]
        pqi_state.available_capital = pqi_state.portfolio_value

    def _close_paper(self, reason):
        position = pqi_state.paper_position
        if not position:
            return
        pnl = float(position.get("pnl", 0))
        pqi_state.daily_pnl = pnl
        pqi_state.portfolio_value = pqi_state.trading_capital + pnl
        pqi_state.available_capital = pqi_state.portfolio_value
        pqi_state.paper_position = None
        pqi_state.open_positions = 0
        pqi_state.execution_log.insert(0, {"time": utc_now().isoformat(), "symbol": pqi_state.symbol, "side": "CLOSE", "status": f"PAPER CLOSE: {reason}", "pnl": pnl})
        pqi_state.execution_log = pqi_state.execution_log[:50]

    async def _run_live(self):
        from app.trading.trading_service import TradingService
        account = self._live_account
        pqi_state.exchange_connected = True
        pqi_state.connection_status = "CONNECTED"
        pqi_state.market_status = "ONLINE"
        pqi_state.mode = "live"
        service = TradingService()
        while not self._stop_event.is_set():
            if pqi_state.status == "PAUSED":
                await asyncio.sleep(1)
                continue
            if pqi_state.status != "ACTIVE":
                break
            result = await service.run(account, capital=pqi_state.trading_capital, symbol=pqi_state.symbol)
            analysis = result.get("analysis") or {}
            snapshot = analysis.get("snapshot")
            if snapshot:
                pqi_state.last_price = float((snapshot.ticker or {}).get("lastPrice", 0))
                tf = snapshot.timeframes.get("1h")
                if tf:
                    candles = tf.candles
                    pqi_state.candles = [
                        {"time": int(c[0]), "open": float(c[1]), "high": float(c[2]), "low": float(c[3]), "close": float(c[4]), "volume": float(c[5])}
                        for c in candles[-120:]
                    ]
            decision = analysis.get("decision")
            if decision:
                pqi_state.confidence = float(decision.confidence)
                pqi_state.current_decision = decision.action if decision.should_execute else "WAIT"
                pqi_state.intelligence = {
                    "trend": getattr(analysis.get("trend"), "overall_direction", ""),
                    "momentum": getattr(analysis.get("momentum"), "overall_direction", ""),
                    "volume": getattr(analysis.get("volume"), "overall_direction", ""),
                    "volatility": getattr(analysis.get("volatility"), "overall_regime", ""),
                    "personality": getattr(analysis.get("personality"), "personality", ""),
                    "opportunity_score": getattr(analysis.get("opportunity"), "score", 0),
                    "reason": decision.reason,
                    "signal": decision.action,
                    "entry": pqi_state.last_price,
                }
            pqi_state.available_capital = float(result.get("account_balance", pqi_state.available_capital) or 0)
            pqi_state.portfolio_value = pqi_state.available_capital
            pqi_state.starting_capital = pqi_state.trading_capital
            pqi_state.current_task = "Live Trading Cycle"
            pqi_state.signals_analysed += 1
            pqi_state.next_scan = utc_now() + timedelta(seconds=8)
            await asyncio.sleep(8)

    @staticmethod
    def _normalise_symbol(symbol):
        symbol = (symbol or "BTCUSDT").upper().strip()
        if "/" in symbol:
            return symbol
        if symbol.endswith("USDT"):
            return symbol[:-4] + "/USDT"
        return symbol


engine = PQIEngine()
