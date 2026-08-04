from dataclasses import dataclass

from app.models.market_snapshot import MarketSnapshot


@dataclass(slots=True)
class MomentumResult:

    timeframe: str

    direction: str

    strength: float

    rsi: float

    macd: float

    macd_signal: float

    macd_histogram: float


@dataclass(slots=True)
class MomentumAnalysis:

    momentum: dict

    overall_direction: str

    confidence: float

    strength: float

    exhaustion: bool


class MomentumEngine:
    """
    Multi-Timeframe Momentum Engine.

    Uses precomputed indicators from IndicatorService.

    No indicator calculations occur here.
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

        weighted_strength = 0

        exhaustion = False

        total_weight = sum(
            self.TIMEFRAME_WEIGHT.values()
        )

        for tf, tf_data in snapshot.timeframes.items():

            ind = tf_data.indicators

            direction = self._direction(ind)

            strength = self._strength(ind)

            if direction == "BULLISH":

                bullish += self.TIMEFRAME_WEIGHT[tf]

            elif direction == "BEARISH":

                bearish += self.TIMEFRAME_WEIGHT[tf]

            weighted_strength += (

                strength *

                self.TIMEFRAME_WEIGHT[tf]

            )

            if ind.rsi >= 80 or ind.rsi <= 20:

                exhaustion = True

            results[tf] = MomentumResult(

                timeframe=tf,

                direction=direction,

                strength=strength,

                rsi=ind.rsi,

                macd=ind.macd,

                macd_signal=ind.macd_signal,

                macd_histogram=ind.macd_histogram,

            )

        if bullish > bearish:

            overall = "BULLISH"

            confidence = bullish / total_weight

        elif bearish > bullish:

            overall = "BEARISH"

            confidence = bearish / total_weight

        else:

            overall = "SIDEWAYS"

            confidence = 0.5

        return MomentumAnalysis(

            momentum=results,

            overall_direction=overall,

            confidence=round(

                confidence * 100,

                2,

            ),

            strength=round(

                weighted_strength / total_weight,

                2,

            ),

            exhaustion=exhaustion,

        )

    def _direction(
        self,
        ind,
    ):

        if (

            ind.macd >

            ind.macd_signal

            and

            ind.rsi >= 55

        ):

            return "BULLISH"

        elif (

            ind.macd <

            ind.macd_signal

            and

            ind.rsi <= 45

        ):

            return "BEARISH"

        return "SIDEWAYS"

    def _strength(
        self,
        ind,
    ):

        strength = abs(ind.macd_histogram)

        if ind.adx >= 40:

            strength *= 1.2

        elif ind.adx < 20:

            strength *= 0.6

        return round(strength, 2)