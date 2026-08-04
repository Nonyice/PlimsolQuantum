from dataclasses import dataclass


@dataclass
class TimeframeAnalysis:

    timeframe: str
    candles: list


class MultiTimeframeEngine:
    """
    Downloads market data from multiple
    timeframes.

    Every intelligence engine will consume
    these candles instead of downloading
    their own.
    """

    TIMEFRAMES = [

        "1m",

        "5m",

        "15m",

        "1h",

        "4h",

        "1d",

    ]

    async def analyse(
        self,
        exchange,
        symbol,
    ):

        market = {}

        for tf in self.TIMEFRAMES:

            candles = await exchange.get_candles(

                symbol=symbol,

                interval=tf,

                limit=300,

            )

            market[tf] = TimeframeAnalysis(

                timeframe=tf,

                candles=candles,

            )

        return market