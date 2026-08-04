from app.enums.exchange import Exchange
from app.enums.market_type import MarketType

from app.trading.exchanges.binance_spot import (
    BinanceSpotAdapter,
)
from app.trading.exchanges.binance_futures import (
    BinanceFuturesAdapter,
)
from app.trading.exchanges.bybit_spot import (
    BybitSpotAdapter,
)
from app.trading.exchanges.bybit_futures import (
    BybitFuturesAdapter,
)


class ExchangeFactory:

    @staticmethod
    def create(
        exchange,
        market_type,
        api_key,
        api_secret,
        testnet=False,
    ):

        if exchange == Exchange.BINANCE:

            if market_type == MarketType.SPOT:

                return BinanceSpotAdapter(

                    api_key=api_key,

                    api_secret=api_secret,

                    testnet=testnet,

                )

            if market_type == MarketType.FUTURES:

                return BinanceFuturesAdapter(

                    api_key=api_key,

                    api_secret=api_secret,

                    testnet=testnet,

                )

        if exchange == Exchange.BYBIT:

            if market_type == MarketType.SPOT:

                return BybitSpotAdapter(

                    api_key=api_key,

                    api_secret=api_secret,

                    testnet=testnet,

                )

            if market_type == MarketType.FUTURES:

                return BybitFuturesAdapter(

                    api_key=api_key,

                    api_secret=api_secret,

                    testnet=testnet,

                )

        raise ValueError(

            f"{exchange.value} / "

            f"{market_type.value} "

            "is not supported."

        )