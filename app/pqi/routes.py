from __future__ import annotations

import asyncio

from flask import Blueprint, jsonify, request, session
from flask_login import current_user, login_required

from app.enums.exchange import Exchange
from app.enums.market_type import MarketType
from app.models.trading_account import TradingAccount
from app.pqi.engine import engine
from app.services.public_market_service import PublicMarketService

pqi_bp = Blueprint("pqi", __name__)


def _default_account():
    return (
        TradingAccount.query.filter_by(user_id=current_user.id, active=True, is_default=True).first()
        or TradingAccount.query.filter_by(user_id=current_user.id, active=True).first()
    )


@pqi_bp.route("/api/pqi/state", methods=["GET"])
@login_required
def state():
    return jsonify(engine.snapshot())


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
    active_trial = current_user.active_trial
    if active_trial:
        selected = float(engine.snapshot().trading_capital or session.get("pqi_paper_capital", 1000))
        return jsonify({
            "mode": "trial",
            "minimum": 10,
            "available": selected,
            "selected": selected,
            "currency": "USDT",
            "can_trade": True,
        })

    account = _default_account()
    if account is None:
        return jsonify({"mode": "live", "available": 0, "selected": 0, "minimum": 10, "currency": "USDT", "can_trade": False})

    try:
        from app.trading.exchanges.factory import ExchangeFactory
        credentials = account.get_credentials()
        adapter = ExchangeFactory.create(account.exchange, account.market_type, credentials["api_key"], credentials["api_secret"], account.is_testnet)
        balances = asyncio.run(adapter.get_account_balance())
        available = next((float(x.get("free", 0)) for x in balances if x.get("asset") == "USDT"), 0.0)
        return jsonify({
            "mode": "live",
            "available": available,
            "selected": float(engine.snapshot().trading_capital or min(available, 100.0)),
            "minimum": 10,
            "currency": "USDT",
            "can_trade": bool(account.can_trade),
            "exchange": account.exchange.value,
            "account_id": str(account.id),
        })
    except Exception as exc:
        return jsonify({"mode": "live", "available": 0, "selected": 0, "minimum": 10, "currency": "USDT", "can_trade": bool(account.can_trade), "error": str(exc)}), 502


@pqi_bp.route("/api/pqi/config", methods=["POST"])
@login_required
def configure():
    data = request.get_json(silent=True) or {}
    exchange = (data.get("exchange") or "binance").strip().lower()
    market = (data.get("market") or "").strip().upper()
    market = market.replace("/", "")
    if not market:
        return jsonify({"success": False, "error": "Select a trading pair."}), 400
    market_type = (data.get("market_type") or "spot").strip().lower()
    active_trial = current_user.active_trial

    # The dashboard can apply the market configuration before the user
    # explicitly changes capital. In that case preserve the existing
    # trial/session capital instead of rejecting the configuration.
    raw_capital = data.get("capital")
    if raw_capital in (None, ""):
        raw_capital = session.get("pqi_paper_capital") or engine.snapshot().trading_capital or 1000

    try:
        capital_value = float(raw_capital)
    except (TypeError, ValueError):
        return jsonify({"success": False, "error": "Enter a valid trading capital amount."}), 400

    if capital_value < 10:
        return jsonify({"success": False, "error": "Minimum trading capital is $10."}), 400

    if active_trial:
        try:
            available_markets = asyncio.run(PublicMarketService.markets(exchange, market_type))
            if market not in available_markets:
                return jsonify({"success": False, "error": f"{market} is not available on {exchange} {market_type}."}), 400
        except Exception as exc:
            return jsonify({"success": False, "error": f"Unable to validate trading pair: {exc}"}), 502
        session["pqi_paper_capital"] = capital_value
        engine.configure(exchange, market, market_type, capital_value)
        return jsonify({"success": True, "state": engine.snapshot()})

    account = _default_account()
    if account is None:
        return jsonify({"success": False, "error": "Connect an exchange account before going live."}), 400
    if not account.can_trade:
        return jsonify({"success": False, "error": "Live trading is not authorized for this account yet."}), 403

    info = capital().get_json()
    available = float(info.get("available", 0))
    if capital_value > available:
        return jsonify({"success": False, "error": f"Insufficient capital. Available USDT: ${available:,.2f}."}), 400
    if account.market_type.value != market_type:
        market_type = account.market_type.value
    try:
        available_markets = asyncio.run(PublicMarketService.markets(account.exchange.value, market_type))
        if market not in available_markets:
            return jsonify({"success": False, "error": f"{market} is not available on {account.exchange.value} {market_type}."}), 400
    except Exception as exc:
        return jsonify({"success": False, "error": f"Unable to validate trading pair: {exc}"}), 502
    engine.configure(account.exchange.value, market, market_type, capital_value)
    return jsonify({"success": True, "state": engine.snapshot()})


@pqi_bp.route("/api/pqi/engage", methods=["POST"])
@login_required
def engage():
    data = request.get_json(silent=True) or {}
    active_trial = current_user.active_trial
    exchange = (data.get("exchange") or "binance").strip().lower()
    market = (data.get("market") or "BTCUSDT").strip().upper()
    market_type = (data.get("market_type") or "spot").strip().lower()

    try:
        raw_capital = data.get("capital")
        if raw_capital in (None, ""):
            raw_capital = session.get("pqi_paper_capital") or engine.snapshot().trading_capital
        capital_value = float(raw_capital)
    except (TypeError, ValueError):
        return jsonify({"success": False, "error": "Select a valid trading capital amount."}), 400

    if capital_value < 10:
        return jsonify({"success": False, "error": "Select trading capital of at least $10."}), 400

    live_account = None
    exchange_id = "trial"

    if active_trial:
        session["pqi_paper_capital"] = capital_value
        # Trial uses public exchange data; API credentials are never required.
        exchange = exchange if exchange in {"binance", "bybit"} else "binance"
    else:
        account_id = (data.get("exchange_id") or "").strip()
        account = TradingAccount.query.filter_by(id=account_id, user_id=current_user.id, active=True).first() if account_id else None
        account = account or _default_account()
        if account is None:
            return jsonify({"success": False, "error": "Connect an exchange account before going live."}), 400
        if not account.can_trade:
            return jsonify({"success": False, "error": "Live trading is not authorized for this account yet."}), 403
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

    try:
        if exchange not in {"trial", "binance", "bybit"}:
            Exchange(exchange)
        MarketType(market_type)
        available_markets = asyncio.run(PublicMarketService.markets(exchange, market_type))
        compact_market = market.replace("/", "")
        if compact_market not in available_markets:
            return jsonify({"success": False, "error": f"{compact_market} is not available on {exchange} {market_type}."}), 400
        result = engine.engage(exchange, compact_market, exchange_id, market_type, live_account, capital_value)
        return jsonify({"success": True, "state": result})
    except ValueError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"success": False, "error": f"Unable to engage PQI: {exc}"}), 500


@pqi_bp.route("/api/pqi/pause", methods=["POST"])
@login_required
def pause():
    return jsonify(engine.pause())


@pqi_bp.route("/api/pqi/stop", methods=["POST"])
@login_required
def stop():
    return jsonify(engine.stop())
