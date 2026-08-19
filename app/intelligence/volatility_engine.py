from dataclasses import dataclass

from app.models.market_snapshot import MarketSnapshot


@dataclass(slots=True)
class VolatilityResult:

    timeframe: str
    atr: float
    volatility: float
    regime: str
    stop_multiplier: float


@dataclass(slots=True)
class VolatilityAnalysis:

    timeframes: dict

    overall_regime: str

    confidence: float

    recommended_stop_multiplier: float

    explosive: bool


class VolatilityEngine:
    """
    Multi-Timeframe Volatility Engine.

    Uses precomputed ATR and Bollinger Bands.
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

        score = 0

        weighted_stop = 0

        explosive = False

        available_weights = [
            self.TIMEFRAME_WEIGHT[tf]
            for tf in snapshot.timeframes
            if tf in self.TIMEFRAME_WEIGHT
        ]
        total_weight = sum(available_weights) or 1

        for tf, tf_data in snapshot.timeframes.items():

            ind = tf_data.indicators

            regime = self._regime(ind)

            stop = self._stop_multiplier(regime)

            closes = [
                float(c[4])
                for c in tf_data.candles
            ]

            volatility = (

                ind.atr

                / closes[-1]

            ) * 100

            results[tf] = VolatilityResult(

                timeframe=tf,

                atr=ind.atr,

                volatility=round(
                    volatility,
                    2,
                ),

                regime=regime,

                stop_multiplier=stop,

            )

            weight = self.TIMEFRAME_WEIGHT[tf]

            weighted_stop += stop * weight

            if regime == "HIGH":

                score += weight

            elif regime == "LOW":

                score -= weight

            if volatility >= 5:

                explosive = True

        if score > total_weight * 0.25:

            overall = "HIGH"

        elif score < -total_weight * 0.25:

            overall = "LOW"

        else:

            overall = "NORMAL"

        confidence = abs(score) / total_weight

        return VolatilityAnalysis(

            timeframes=results,

            overall_regime=overall,

            confidence=round(
                confidence * 100,
                2,
            ),

            recommended_stop_multiplier=round(

                weighted_stop

                / total_weight,

                2,

            ),

            explosive=explosive,

        )

    def _regime(
        self,
        ind,
    ):

        width = (

            ind.upper_bb

            - ind.lower_bb

        ) / ind.middle_bb

        if width >= 0.08:

            return "HIGH"

        elif width <= 0.03:

            return "LOW"

        return "NORMAL"

    def _stop_multiplier(
        self,
        regime,
    ):

        if regime == "HIGH":

            return 2.5

        elif regime == "LOW":

            return 1.2

        return 1.8