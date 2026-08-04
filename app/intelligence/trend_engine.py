from dataclasses import dataclass

from app.models.market_snapshot import MarketSnapshot


@dataclass(slots=True)
class TrendResult:

    timeframe: str

    direction: str

    strength: float

    ema20: float

    ema50: float

    ema200: float

    adx: float


@dataclass(slots=True)
class TrendAnalysis:

    trends: dict

    overall_direction: str

    alignment_score: float

    confidence: float


class TrendEngine:
    """
    Multi-Timeframe Trend Engine.

    Uses precomputed indicators from IndicatorService.

    DOES NOT calculate indicators.
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

        trends = {}

        bullish = 0

        bearish = 0

        total_weight = sum(
            self.TIMEFRAME_WEIGHT.values()
        )

        weighted_strength = 0

        for tf, tf_data in snapshot.timeframes.items():

            ind = tf_data.indicators

            direction = self._direction(ind)

            strength = self._strength(ind)

            trends[tf] = TrendResult(

                timeframe=tf,

                direction=direction,

                strength=strength,

                ema20=ind.ema20,

                ema50=ind.ema50,

                ema200=ind.ema200,

                adx=ind.adx,

            )

            weight = self.TIMEFRAME_WEIGHT[tf]

            weighted_strength += strength * weight

            if direction == "BULLISH":

                bullish += weight

            elif direction == "BEARISH":

                bearish += weight

        if bullish > bearish:

            overall = "BULLISH"

            confidence = bullish / total_weight

        elif bearish > bullish:

            overall = "BEARISH"

            confidence = bearish / total_weight

        else:

            overall = "SIDEWAYS"

            confidence = 0.5

        alignment = max(
            bullish,
            bearish,
        ) / total_weight

        return TrendAnalysis(

            trends=trends,

            overall_direction=overall,

            alignment_score=round(
                alignment,
                2,
            ),

            confidence=round(
                confidence * 100,
                2,
            ),

        )

    def _direction(
        self,
        ind,
    ):

        if (

            ind.ema20 >

            ind.ema50 >

            ind.ema200

        ):

            return "BULLISH"

        elif (

            ind.ema20 <

            ind.ema50 <

            ind.ema200

        ):

            return "BEARISH"

        return "SIDEWAYS"

    def _strength(
        self,
        ind,
    ):

        if ind.adx >= 40:

            return 1.0

        elif ind.adx >= 30:

            return 0.80

        elif ind.adx >= 20:

            return 0.60

        return 0.30