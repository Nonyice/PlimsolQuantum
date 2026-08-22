from __future__ import annotations

import asyncio

from flask import Blueprint, jsonify, request, session, current_app
from flask_login import current_user, login_required

from app.enums.exchange import Exchange
from app.enums.market_type import MarketType
from app.extensions import db
from app.models.pqi_session import PQISession
from app.models.trading_account import TradingAccount
from app.pqi.engine import engine as legacy_engine
from app.pqi.runtime import runtime_manager
from app.services.public_market_service import PublicMarketService

pqi_bp = Blueprint("pqi", __name__)


def _default_account():
    return (
        TradingAccount.query.filter_by(user_id=current_user.id, active=True, is_default=True).first()
        or TradingAccount.query.filter_by(user_id=current_user.id, active=True).first()
    )


def _active_sessions():
    runtime_manager.ensure_user(current_user.id, current_app._get_current_object())
    return (
        PQISession.query
        .filter_by(user_id=current_user.id, status="ACTIVE")
        .order_by(PQISession.started_at.desc())
        .all()
    )


def _selected_session():
    sessions = _active_sessions()
    selected_id = str(session.get("pqi_session_id") or "")
    selected = next((s for s in sessions if str(s.id) == selected_id), None)
    if selected is None and sessions:
        selected = sessions[0]
        session["pqi_session_id"] = str(selected.id)
    return selected


def _runtime_for_selected():
    selected = _selected_session()
    if selected is None:
        return None, None
    return runtime_manager.ensure(selected, current_app._get_current_object(), current_user.id), selected


@pqi_bp.route("/api/pqi/state", methods=["GET"])
@login_required
def state():
    runtime, selected = _runtime_for_selected()
    if runtime is None:
        return jsonify(legacy_engine.snapshot())
    return jsonify(runtime.snapshot())


@pqi_bp.route("/api/pqi/sessions", methods=["GET"])
@login_required
def session_list():
    items = []
    selected = _selected_session()
    for s in _active_sessions():
        runtime = runtime_manager.get(s.id)
        state_obj = runtime.snapshot() if runtime else None
        items.append({
            "id": str(s.id),
            "mode": s.mode,
            "status": s.status,
            "exchange": s.exchange,
            "market_type": s.market_type,
            "capital": float(s.capital),
            "started_at": s.started_at.isoformat() if s.started_at else None,
            "pair_count": sum(1 for p in s.pairs if p.status in ("OBSERVING", "OPEN")),
            "pairs": [p.symbol for p in s.pairs if p.status in ("OBSERVING", "OPEN")],
            "confidence": float(getattr(state_obj, "confidence", 0) or 0) if state_obj else 0,
            "decision": getattr(state_obj, "current_decision", "WAITING") if state_obj else "WAITING",
            "task": getattr(state_obj, "current_task", "--") if state_obj else "--",
            "selected": bool(selected and s.id == selected.id),
        })
    return jsonify({
        "success": True,
        "sessions": items,
        "selected_session_id": str(selected.id) if selected else None,
        "active_session_count": len(items),
        "max_active_sessions": 4,
        "remaining_session_slots": max(0, 4 - len(items)),
    })


@pqi_bp.route("/api/pqi/session/select", methods=["POST"])
@login_required
def select_session():
    data = request.get_json(silent=True) or {}
    session_id = str(data.get("session_id") or "")
    target = PQISession.query.filter_by(id=session_id, user_id=current_user.id, status="ACTIVE").first()
    if target is None:
        return jsonify({"success": False, "error": "PQI session not found or no longer active."}), 404
    runtime_manager.ensure(target, current_app._get_current_object(), current_user.id)
    session["pqi_session_id"] = str(target.id)
    return jsonify({"success": True, "state": runtime_manager.get(target.id).snapshot()})


@pqi_bp.route("/api/pqi/markets", methods=["GET"])
@login_required
def markets():
    exchange = (request.args.get("exchange") or "binance").lower()
    market_type = (request.args.get("market_type") or "spot").lower()
    try:
        items = asyncio.run(PublicMarketService.markets(exchange, market_type))
        return jsonify({"success": True, "markets": items})
    except Exception as exc:
        return jsonify({"success": False, "markets": [], "error": str(exc)}), 502


@pqi_bp.route("/api/pqi/market-data", methods=["GET"])
@login_required
def market_data():
    exchange = (request.args.get("exchange") or "binance").lower()
    market_type = (request.args.get("market_type") or "spot").lower()
    symbol = (request.args.get("symbol") or "BTCUSDT").upper().replace("/", "")

    async def _fetch():
        return await asyncio.gather(
            PublicMarketService.candles(exchange, market_type, symbol, "1h", 120),
            PublicMarketService.ticker(exchange, market_type, symbol),
        )

    try:
        candles, ticker = asyncio.run(_fetch())
        return jsonify({"success": True, "symbol": symbol, "candles": candles, "ticker": ticker})
    except Exception as exc:
        return jsonify({"success": False, "candles": [], "ticker": {}, "error": str(exc)}), 502


@pqi_bp.route("/api/pqi/capital", methods=["GET"])
@login_required
def capital():
    selected = _selected_session()
    if selected and selected.mode == "trial":
        value = float(selected.capital or 1000)
        return jsonify({"mode": "trial", "available": value, "selected": value, "minimum": 10, "currency": "USDT", "can_trade": True})

    account = _default_account()
    if account is None:
        return jsonify({"mode": "live", "available": 0, "selected": 0, "minimum": 10, "currency": "USDT", "can_trade": False})
    try:
        from app.trading.exchanges.factory import ExchangeFactory
        credentials = account.get_credentials()
        adapter = ExchangeFactory.create(account.exchange, account.market_type, credentials["api_key"], credentials["api_secret"], account.is_testnet)
        balances = asyncio.run(adapter.get_account_balance())
        available = next((float(x.get("free", 0)) for x in balances if x.get("asset") == "USDT"), 0.0)
        selected_value = float(selected.capital) if selected and selected.mode == "live" else min(available, 100.0)
        return jsonify({"mode": "live", "available": available, "selected": selected_value, "minimum": 10, "currency": "USDT", "can_trade": bool(account.can_trade), "exchange": account.exchange.value, "market_type": account.market_type.value, "account_id": str(account.id)})
    except Exception as exc:
        return jsonify({"mode": "live", "available": 0, "selected": 0, "minimum": 10, "currency": "USDT", "can_trade": bool(account.can_trade), "error": str(exc)}), 502


@pqi_bp.route("/api/pqi/config", methods=["POST"])
@login_required
def configure():
    data = request.get_json(silent=True) or {}
    # Configuration is deliberately separate from session creation.
    # Add Trial sends this flag so Apply Market can validate the proposed
    # configuration without mutating the currently running session.
    new_session = bool(data.get("new_session", False))
    exchange = (data.get("exchange") or "binance").strip().lower()
    market = (data.get("market") or "BTC/USDT").strip().upper()
    market_type = (data.get("market_type") or "spot").strip().lower()
    selected = _selected_session()
    mode = (data.get("mode") or (selected.mode if selected else ("trial" if current_user.active_trial else "live"))).lower()
    raw_capital = data.get("capital")
    if raw_capital in (None, ""):
        raw_capital = float(selected.capital) if selected else 1000
    try:
        capital_value = float(raw_capital)
    except (TypeError, ValueError):
        return jsonify({"success": False, "error": "Enter a valid trading capital amount."}), 400
    if capital_value < 10:
        return jsonify({"success": False, "error": "Minimum trading capital is $10."}), 400

    if mode == "trial":
        if not current_user.active_trial:
            return jsonify({"success": False, "error": "An active PQI trial is required for paper trading."}), 403

        # "Apply Market" from Add Trial is configuration-only. It must never
        # mutate the currently selected session or create a new database row.
        if new_session:
            if exchange not in {"binance", "bybit"}:
                return jsonify({"success": False, "error": "Unsupported exchange."}), 400
            try:
                legacy_engine._validate_new_session(current_user.id, market, market_type)
                db.session.rollback()
            except ValueError as exc:
                db.session.rollback()
                return jsonify({"success": False, "error": str(exc)}), 409
            return jsonify({
                "success": True,
                "new_session": True,
                "applied": {
                    "exchange": exchange,
                    "market": market,
                    "market_type": market_type,
                    "capital": capital_value,
                },
            })

        if selected and selected.mode == "trial":
            try:
                legacy_engine._validate_new_session(current_user.id, market, market_type, exclude_session_id=selected.id)
            except ValueError as exc:
                db.session.rollback()
                return jsonify({"success": False, "error": str(exc)}), 409
            runtime = runtime_manager.ensure(selected, current_app._get_current_object(), current_user.id)
            runtime.configure(exchange, market, market_type, capital_value)
            selected.exchange = exchange
            selected.market_type = market_type
            selected.capital = capital_value
            db.session.commit()
            return jsonify({"success": True, "state": runtime.snapshot()})
        return jsonify({"success": True, "state": legacy_engine.snapshot()})

    account = _default_account()
    if account is None:
        return jsonify({"success": False, "error": "Connect an exchange account before going live."}), 400
    if account.market_type.value != market_type:
        market_type = account.market_type.value
    if account.exchange.value != exchange:
        exchange = account.exchange.value
    info = capital().get_json()
    if capital_value > float(info.get("available", 0)):
        return jsonify({"success": False, "error": f"Insufficient capital. Available USDT: ${float(info.get('available', 0)):,.2f}."}), 400
    if selected and selected.mode == "live":
        try:
            legacy_engine._validate_new_session(current_user.id, market, market_type, exclude_session_id=selected.id)
        except ValueError as exc:
            db.session.rollback()
            return jsonify({"success": False, "error": str(exc)}), 409
        runtime = runtime_manager.ensure(selected, current_app._get_current_object(), current_user.id)
        runtime.configure(exchange, market, market_type, capital_value)
        selected.exchange = exchange
        selected.market_type = market_type
        selected.capital = capital_value
        db.session.commit()
        return jsonify({"success": True, "state": runtime.snapshot()})
    return jsonify({"success": True})


@pqi_bp.route("/api/pqi/engage", methods=["POST"])
@login_required
def engage():
    data = request.get_json(silent=True) or {}
    selected = _selected_session()
    mode = (data.get("mode") or (selected.mode if selected else ("trial" if current_user.active_trial else "live"))).strip().lower()
    exchange = (data.get("exchange") or "binance").strip().lower()
    new_session = bool(data.get("new_session", False))
    raw_market = data.get("market")
    if new_session and not raw_market:
        return jsonify({"success": False, "error": "Select a trading pair before creating a new PQI session."}), 400
    market = (raw_market or "BTCUSDT").strip().upper()
    market_type = (data.get("market_type") or "spot").strip().lower()

    try:
        capital_value = float(data.get("capital") or (float(selected.capital) if selected else 1000))
    except (TypeError, ValueError):
        return jsonify({"success": False, "error": "Select a valid trading capital amount."}), 400
    if capital_value < 10:
        return jsonify({"success": False, "error": "Select trading capital of at least $10."}), 400

    live_account = None
    exchange_id = "trial"

    if mode == "trial":
        if not current_user.active_trial:
            return jsonify({"success": False, "error": "Your PQI trial is not active."}), 403
        exchange = exchange if exchange in {"binance", "bybit"} else "binance"
        if not new_session and selected and selected.mode == "trial":
            target = selected
        else:
            target = None
    else:
        account_id = (data.get("exchange_id") or "").strip()
        account = TradingAccount.query.filter_by(id=account_id, user_id=current_user.id, active=True).first() if account_id else None
        account = account or _default_account()
        if account is None:
            return jsonify({"success": False, "error": "Connect an exchange account before going live."}), 400
        live_account = account
        exchange = account.exchange.value
        market_type = account.market_type.value
        exchange_id = str(account.id)
        try:
            from app.trading.exchanges.factory import ExchangeFactory
            credentials = account.get_credentials()
            adapter = ExchangeFactory.create(account.exchange, account.market_type, credentials["api_key"], credentials["api_secret"], account.is_testnet)
            balances = asyncio.run(adapter.get_account_balance())
            available = next((float(x.get("free", 0)) for x in balances if x.get("asset") == "USDT"), 0.0)
            if capital_value > available:
                return jsonify({"success": False, "error": f"Insufficient capital. Available USDT: ${available:,.2f}."}), 400
        except Exception as exc:
            return jsonify({"success": False, "error": f"Unable to verify exchange capital: {exc}"}), 502
        target = None if new_session or not selected or selected.mode != "live" else selected

    try:
        if target is not None:
            runtime = runtime_manager.ensure(target, current_app._get_current_object(), current_user.id)
            runtime.configure(exchange, market, market_type, capital_value)
            result = runtime.engage(exchange, market, exchange_id, market_type, live_account, capital_value, current_user.id, current_app._get_current_object(), new_session=False)
        else:
            runtime = __import__("app.pqi.runtime", fromlist=["runtime_manager"]).runtime_manager
            # Temporary engine creates the persistent record, then is registered under its id.
            from app.pqi.engine import PQIEngine
            from app.pqi.state import PQIState
            temp = PQIEngine(state=PQIState())
            result = temp.engage(exchange, market, exchange_id, market_type, live_account, capital_value, current_user.id, current_app._get_current_object(), new_session=True)
            session_id = result.session_id
            runtime._engines[str(session_id)] = temp
            session["pqi_session_id"] = str(session_id)
            return jsonify({"success": True, "state": result})
    except ValueError as exc:
        db.session.rollback()
        return jsonify({"success": False, "error": str(exc)}), 409
    except Exception as exc:
        db.session.rollback()
        return jsonify({"success": False, "error": f"Unable to engage PQI: {exc}"}), 500

    session["pqi_session_id"] = str(result.session_id)
    return jsonify({"success": True, "state": result})


@pqi_bp.route("/api/pqi/pair/add", methods=["POST"])
@login_required
def add_pair():
    data = request.get_json(silent=True) or {}
    symbol = (data.get("symbol") or data.get("market") or "").strip().upper()
    if not symbol:
        return jsonify({"success": False, "error": "Select a trading pair."}), 400

    runtime, selected = _runtime_for_selected()
    if runtime is None or selected is None:
        return jsonify({"success": False, "error": "No active PQI session selected."}), 400
    try:
        pair = runtime.add_pair(symbol)
        return jsonify({
            "success": True,
            "pair": {"id": str(pair.id), "symbol": pair.symbol, "status": pair.status},
            "state": runtime.snapshot(),
        })
    except ValueError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400
    except Exception as exc:
        db.session.rollback()
        return jsonify({"success": False, "error": str(exc)}), 500


@pqi_bp.route("/api/pqi/pause", methods=["POST"])
@login_required
def pause():
    runtime, selected = _runtime_for_selected()
    return jsonify(runtime.pause() if runtime else legacy_engine.pause())


@pqi_bp.route("/api/pqi/stop", methods=["POST"])
@login_required
def stop():
    runtime, selected = _runtime_for_selected()
    result = runtime.stop() if runtime else legacy_engine.stop()
    if selected:
        session.pop("pqi_session_id", None)
        runtime_manager.remove(selected.id)
    return jsonify(result)
