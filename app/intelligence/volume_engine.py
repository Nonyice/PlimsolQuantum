from dataclasses import dataclass

from app.models.market_snapshot import MarketSnapshot


@dataclass(slots=True)
class VolumeResult:

    timeframe: str

    average_volume: float

    current_volume: float

    relative_volume: float

    buy_pressure: float

    sell_pressure: float

    direction: str

    confirmation: bool


@dataclass(slots=True)
class VolumeAnalysis:

    volumes: dict

    overall_direction: str

    confidence: float

    accumulation: bool

    distribution: bool

    confirmed: bool


class VolumeEngine:
    """
    Institutional Multi-Timeframe Volume Engine.

    Uses:

    - Volume
    - ADX
    - ATR
    - Bollinger Width

    from IndicatorService.
    """

    TIMEFRAME_WEIGHT = {

        "1m": 1,

        "5m": 2,

        "15m": 3,

        "1h": 5,

        "4h": 8,

        "1d": 13,

    }

    def analyse(
        self,
        snapshot: MarketSnapshot,
    ):

        results = {}

        bullish = 0

        bearish = 0

        confirmations = 0

        accumulation = False

        distribution = False

        available_weights = [
            self.TIMEFRAME_WEIGHT[tf]
            for tf in snapshot.timeframes
            if tf in self.TIMEFRAME_WEIGHT
        ]
        total_weight = sum(available_weights) or 1

        for tf, tf_data in snapshot.timeframes.items():

            ind = tf_data.indicators

            result = self._analyse_timeframe(

                tf,

                tf_data.candles,

                ind,

            )

            results[tf] = result

            weight = self.TIMEFRAME_WEIGHT[tf]

            if result.direction == "BULLISH":

                bullish += weight

            elif result.direction == "BEARISH":

                bearish += weight

            if result.confirmation:

                confirmations += weight

            if (

                result.relative_volume > 1.5

                and

                result.buy_pressure > 60

                and

                ind.adx >= 25

            ):

                accumulation = True

            if (

                result.relative_volume > 1.5

                and

                result.sell_pressure > 60

                and

                ind.adx >= 25

            ):

                distribution = True

        if bullish > bearish:

            direction = "BULLISH"

            confidence = bullish / total_weight

        elif bearish > bullish:

            direction = "BEARISH"

            confidence = bearish / total_weight

        else:

            direction = "SIDEWAYS"

            confidence = 0.5

        confirmed = (

            confirmations

            >= total_weight * 0.60

        )

        return VolumeAnalysis(

            volumes=results,

            overall_direction=direction,

            confidence=round(

                confidence * 100,

                2,

            ),

            accumulation=accumulation,

            distribution=distribution,

            confirmed=confirmed,

        )

    def _analyse_timeframe(

        self,

        timeframe,

        candles,

        ind,

    ):

        volumes = [

            float(c[5])

            for c in candles

        ]

        opens = [

            float(c[1])

            for c in candles

        ]

        closes = [

            float(c[4])

            for c in candles

        ]

        current_volume = volumes[-1]

        average_volume = (

            sum(volumes[:-1])

            / max(

                len(volumes[:-1]),

                1,

            )

        )

        relative_volume = (

            current_volume

            / average_volume

            if average_volume

            else 1

        )

        buy = 0

        sell = 0

        for o, c in zip(opens, closes):

            if c >= o:

                buy += 1

            else:

                sell += 1

        total = buy + sell

        buy_pressure = (

            buy

            / total

        ) * 100

        sell_pressure = (

            sell

            / total

        ) * 100

        if buy_pressure > sell_pressure:

            direction = "BULLISH"

        elif sell_pressure > buy_pressure:

            direction = "BEARISH"

        else:

            direction = "SIDEWAYS"

        confirmation = (

            relative_volume >= 1.20

            and

            ind.adx >= 20

        )

        return VolumeResult(

            timeframe=timeframe,

            average_volume=round(

                average_volume,

                2,

            ),

            current_volume=round(

                current_volume,

                2,

            ),

            relative_volume=round(

                relative_volume,

                2,

            ),

            buy_pressure=round(

                buy_pressure,

                2,

            ),

            sell_pressure=round(

                sell_pressure,

                2,

            ),

            direction=direction,

            confirmation=confirmation,

        )