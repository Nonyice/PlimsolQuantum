from statistics import mean, stdev


class TrendIntelligence:
    """
    Performs technical analysis on market data.

    This class converts raw Binance candle data into
    meaningful market intelligence used by PQI.
    """

    def analyse(self, candles):

        closes = [float(c[4]) for c in candles]
        highs = [float(c[2]) for c in candles]
        lows = [float(c[3]) for c in candles]
        opens = [float(c[1]) for c in candles]
        volumes = [float(c[5]) for c in candles]

        trend = self._trend(closes)

        return {
            "trend": trend,
            "trend_strength": self._trend_strength(closes),
            "momentum": self._momentum(closes),
            "volume": self._average_volume(volumes),
            "volatility": self._volatility(closes),
            "support": self._support(lows),
            "resistance": self._resistance(highs),
            "confidence": self._confidence(
                closes,
                opens,
                volumes
            ),
            "healthy": self._healthy(closes, volumes),
            "reasons": self._reasons(
                trend,
                closes,
                volumes
            )
        }

    # ----------------------------------------------------
    # Trend
    # ----------------------------------------------------

    def _trend(self, closes):

        sma20 = mean(closes[-20:])
        sma50 = mean(closes[-50:])

        if sma20 > sma50:
            return "BULLISH"

        if sma20 < sma50:
            return "BEARISH"

        return "SIDEWAYS"

    def _trend_strength(self, closes):

        sma20 = mean(closes[-20:])
        sma50 = mean(closes[-50:])

        return abs((sma20 - sma50) / sma50) * 100

    # ----------------------------------------------------
    # Momentum
    # ----------------------------------------------------

    def _momentum(self, closes):

        return (
            (closes[-1] - closes[-14])
            / closes[-14]
        ) * 100

    # ----------------------------------------------------
    # Volume
    # ----------------------------------------------------

    def _average_volume(self, volumes):

        return mean(volumes)

    # ----------------------------------------------------
    # Volatility
    # ----------------------------------------------------

    def _volatility(self, closes):

        return stdev(closes)

    # ----------------------------------------------------
    # Support
    # ----------------------------------------------------

    def _support(self, lows):

        return min(lows)

    # ----------------------------------------------------
    # Resistance
    # ----------------------------------------------------

    def _resistance(self, highs):

        return max(highs)

    # ----------------------------------------------------
    # Confidence
    # ----------------------------------------------------

    def _confidence(
        self,
        closes,
        opens,
        volumes
    ):

        score = 0

        if closes[-1] > opens[-1]:
            score += 20

        if mean(closes[-20:]) > mean(closes[-50:]):
            score += 30

        if volumes[-1] > mean(volumes):
            score += 25

        momentum = abs(self._momentum(closes))

        score += min(momentum, 25)

        return min(score, 100)

    # ----------------------------------------------------
    # Market Health
    # ----------------------------------------------------

    def _healthy(
        self,
        closes,
        volumes
    ):

        if len(closes) < 50:
            return False

        if mean(volumes) <= 0:
            return False

        return True

    # ----------------------------------------------------
    # Reasons
    # ----------------------------------------------------

    def _reasons(
        self,
        trend,
        closes,
        volumes
    ):

        reasons = []

        if trend == "BULLISH":
            reasons.append("20 SMA above 50 SMA.")

        elif trend == "BEARISH":
            reasons.append("20 SMA below 50 SMA.")

        else:
            reasons.append("Market is ranging.")

        if volumes[-1] > mean(volumes):
            reasons.append("Trading volume is above average.")

        if self._momentum(closes) > 0:
            reasons.append("Positive price momentum.")

        else:
            reasons.append("Negative price momentum.")

        return reasons