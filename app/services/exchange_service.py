"""Exchange connectivity and credential validation."""

from __future__ import annotations

import ccxt

from app.enums.exchange import Exchange
from app.enums.market import MarketType


class ExchangeService:
    @staticmethod
    def test_connection(
        exchange,
        api_key,
        api_secret,
        passphrase=None,
        testnet=False,
        market_type=MarketType.SPOT,
    ):
        try:
            exchange = Exchange(exchange)
        except (ValueError, TypeError):
            return {"success": False, "message": "Unsupported exchange."}

        if exchange == Exchange.BINANCE:
            return ExchangeService._test_binance(
                api_key, api_secret, testnet, market_type
            )

        if exchange == Exchange.BYBIT:
            return ExchangeService._test_bybit(
                api_key, api_secret, passphrase, testnet, market_type
            )

        return {"success": False, "message": "Exchange is not supported."}

    @staticmethod
    def _test_binance(api_key, api_secret, testnet=False, market_type=MarketType.SPOT):
        try:
            client = ccxt.binance({
                "apiKey": api_key,
                "secret": api_secret,
                "enableRateLimit": True,
                "options": {
                    "defaultType": "future" if market_type == MarketType.FUTURES else "spot",
                    # Credential validation must not require Binance's
                    # authenticated SAPI currency/config endpoint.
                    # CCXT may call /sapi/v1/capital/config/getall
                    # while load_markets() fetches currencies, even though
                    # normal spot/futures account access is valid.
                    "fetchCurrencies": False,
                },
            })
            if testnet:
                client.set_sandbox_mode(True)
            client.load_markets()
            balance = client.fetch_balance()
            return {
                "success": True,
                "message": "Binance connection successful.",
                "balance": balance,
            }
        except Exception as exc:
            return {"success": False, "message": str(exc)}

    @staticmethod
    def _test_bybit(
        api_key,
        api_secret,
        passphrase=None,
        testnet=False,
        market_type=MarketType.SPOT,
    ):
        try:
            config = {
                "apiKey": api_key,
                "secret": api_secret,
                "enableRateLimit": True,
                "options": {
                    "defaultType": "swap" if market_type == MarketType.FUTURES else "spot"
                },
            }
            if passphrase:
                config["password"] = passphrase

            client = ccxt.bybit(config)
            if testnet:
                client.set_sandbox_mode(True)
            client.load_markets()
            balance = client.fetch_balance()
            return {
                "success": True,
                "message": "Bybit connection successful.",
                "balance": balance,
            }
        except Exception as exc:
            return {"success": False, "message": str(exc)}
