import asyncio

from app.intelligence.indicator_service import IndicatorService
from app.models.market_snapshot import (
    MarketSnapshot,
    TimeframeData,
)
from app.trading.exchanges.factory import ExchangeFactory


class MarketObserver:
    """
    Downloads market data once and enriches it with indicators.
    """

    TIMEFRAMES = (
        "1m",
        "5m",
        "15m",
        "1h",
        "4h",
        "1d",
    )

    def __init__(self):

        self.indicators = IndicatorService()

    async def observe(
        self,
        trading_account,
    ):

        exchange = ExchangeFactory.create(

            exchange=trading_account.exchange,

            market_type=trading_account.market_type,

            api_key=trading_account.api_key,

            api_secret=trading_account.api_secret,

            testnet=trading_account.is_testnet,

        )

        await exchange.connect()

        symbol = trading_account.symbol

        candle_tasks = [

            exchange.get_candles(

                symbol=symbol,

                interval=tf,

                limit=300,

            )

            for tf in self.TIMEFRAMES

        ]

        extra_tasks = [

            exchange.get_24hr_ticker(symbol),

            exchange.get_order_book(symbol),

            exchange.get_recent_trades(symbol),

            exchange.get_exchange_info(),

            exchange.get_server_time(),

        ]

        results = await asyncio.gather(

            *(candle_tasks + extra_tasks)

        )

        snapshot = MarketSnapshot(

            symbol=symbol,

            exchange=trading_account.exchange.value,

        )

        # -------------------------------
        # Build timeframe objects
        # -------------------------------

        for index, tf in enumerate(self.TIMEFRAMES):

            candles = results[index]

            indicators = self.indicators.calculate(
                candles
            )

            snapshot.timeframes[tf] = TimeframeData(

                timeframe=tf,

                candles=candles,

                indicators=indicators,

            )

        offset = len(self.TIMEFRAMES)

        snapshot.ticker = results[offset]

        snapshot.order_book = results[offset + 1]

        snapshot.trades = results[offset + 2]

        snapshot.exchange_info = results[offset + 3]

        snapshot.server_time = results[offset + 4]

        return snapshot