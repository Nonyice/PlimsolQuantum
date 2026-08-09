"""
Exchange connection service for PlimsolQuantum.
"""

import ccxt

from app.enums.exchange import Exchange
from app.enums.market_type import MarketType


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
        if exchange == Exchange.BINANCE:

            return ExchangeService._test_binance(
                api_key=api_key,
                api_secret=api_secret,
                testnet=testnet,
                market_type=market_type,
            )

        if exchange == Exchange.BYBIT:

            return ExchangeService._test_bybit(
                api_key=api_key,
                api_secret=api_secret,
                passphrase=passphrase,
                testnet=testnet,
                market_type=market_type,
            )

        return {
            "success": False,
            "message": "Exchange is not supported.",
        }

    @staticmethod
    def _test_binance(
        api_key,
        api_secret,
        testnet=False,
        market_type=MarketType.SPOT,
    ):
        try:

            options = {
                "defaultType": (
                    "future"
                    if market_type == MarketType.FUTURES
                    else "spot"
                )
            }

            exchange = ccxt.binance({
                "apiKey": api_key,
                "secret": api_secret,
                "enableRateLimit": True,
                "options": options,
            })

            if testnet:
                exchange.set_sandbox_mode(True)

            exchange.load_markets()

            balance = exchange.fetch_balance()

            return {
                "success": True,
                "message": "Binance connection successful.",
                "balance": balance,
            }

        except Exception as exc:

            return {
                "success": False,
                "message": str(exc),
            }

    @staticmethod
    def _test_bybit(
        api_key,
        api_secret,
        passphrase=None,
        testnet=False,
        market_type=MarketType.SPOT,
    ):
        try:

            options = {
                "defaultType": (
                    "swap"
                    if market_type == MarketType.FUTURES
                    else "spot"
                )
            }

            exchange = ccxt.bybit({
                "apiKey": api_key,
                "secret": api_secret,
                "enableRateLimit": True,
                "options": options,
            })

            if testnet:
                exchange.set_sandbox_mode(True)

            exchange.load_markets()

            balance = exchange.fetch_balance()

            return {
                "success": True,
                "message": "Bybit connection successful.",
                "balance": balance,
            }

        except Exception as exc:

            return {
                "success": False,
                "message": str(exc),
            }