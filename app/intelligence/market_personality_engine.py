from dataclasses import dataclass


@dataclass(slots=True)
class MarketPersonality:

    personality: str

    confidence: float

    bullish: bool

    bearish: bool

    tradable: bool

    description: str


class MarketPersonalityEngine:
    """
    Determines the current personality of the market.

    This engine combines every other engine into one
    institutional market classification.

    Future versions will include:

    • Wyckoff
    • Smart Money Concepts
    • Order Blocks
    • Liquidity Sweeps
    • Fair Value Gaps
    """

    def analyse(

        self,

        trend,

        momentum,

        volume,

        volatility,

        support,

    ):

        personality = "NEUTRAL"

        confidence = 50.0

        bullish = False

        bearish = False

        tradable = False

        description = "No clear market structure."

        # ----------------------------------------------------
        # Institutional Accumulation
        # ----------------------------------------------------

        if (

            trend.overall_direction == "BULLISH"

            and

            momentum.overall_direction == "BULLISH"

            and

            volume.accumulation

            and

            support.market_location == "AT_SUPPORT"

        ):

            personality = "ACCUMULATION"

            confidence = 95

            bullish = True

            tradable = True

            description = (
                "Institutions appear to be accumulating."
            )

        # ----------------------------------------------------
        # Distribution
        # ----------------------------------------------------

        elif (

            trend.overall_direction == "BEARISH"

            and

            momentum.overall_direction == "BEARISH"

            and

            volume.distribution

            and

            support.market_location == "AT_RESISTANCE"

        ):

            personality = "DISTRIBUTION"

            confidence = 95

            bearish = True

            tradable = True

            description = (
                "Institutions appear to be distributing."
            )

        # ----------------------------------------------------
        # Healthy Uptrend
        # ----------------------------------------------------

        elif (

            trend.overall_direction == "BULLISH"

            and

            momentum.overall_direction == "BULLISH"

            and

            volume.confirmed

            and

            volatility.overall_regime != "HIGH"

        ):

            personality = "HEALTHY_UPTREND"

            confidence = 90

            bullish = True

            tradable = True

            description = (
                "Strong bullish trend with healthy momentum."
            )

        # ----------------------------------------------------
        # Healthy Downtrend
        # ----------------------------------------------------

        elif (

            trend.overall_direction == "BEARISH"

            and

            momentum.overall_direction == "BEARISH"

            and

            volume.confirmed

            and

            volatility.overall_regime != "HIGH"

        ):

            personality = "HEALTHY_DOWNTREND"

            confidence = 90

            bearish = True

            tradable = True

            description = (
                "Strong bearish trend with healthy momentum."
            )

        # ----------------------------------------------------
        # Developing trend continuation
        # ----------------------------------------------------
        # This branch is intentionally part of the same if/elif chain as the
        # healthy-trend rules above. The previous standalone `if` overwrote a
        # HEALTHY_UPTREND/HEALTHY_DOWNTREND confidence with a fixed 76%.
        # Confidence is now derived from the actual 1h trend strength and
        # supporting evidence instead of a hard-coded value.
        anchor = trend.trends.get("1h")

        def continuation_confidence(anchor):
            adx = float(anchor.adx or 0)
            adx_quality = max(0.0, min(1.0, (adx - 18.0) / 22.0))
            alignment = max(0.0, min(1.0, float(trend.alignment_score or 0)))
            momentum_quality = max(0.0, min(1.0, float(momentum.confidence or 0) / 100.0))
            volume_quality = max(0.0, min(1.0, float(volume.confidence or 0) / 100.0))
            value = 58 + (14 * alignment) + (13 * adx_quality) + (10 * momentum_quality) + (5 * volume_quality)
            if volatility.overall_regime == "NORMAL":
                value += 3
            elif volatility.overall_regime == "HIGH" and volume.confirmed:
                value += 1
            return round(min(value, 94), 2)

        if (
            personality == "NEUTRAL"
            and
            trend.overall_direction == "BULLISH"
            and momentum.overall_direction == "BULLISH"
            and anchor is not None
            and float(anchor.adx or 0) >= 18
            and volatility.overall_regime != "HIGH"
        ):
            personality = "TREND_CONTINUATION"
            confidence = continuation_confidence(anchor)
            bullish = True
            tradable = True
            description = "Developing bullish 1h trend with aligned momentum."

        elif (
            trend.overall_direction == "BEARISH"
            and momentum.overall_direction == "BEARISH"
            and anchor is not None
            and float(anchor.adx or 0) >= 18
            and volatility.overall_regime != "HIGH"
        ):
            personality = "TREND_CONTINUATION"
            confidence = continuation_confidence(anchor)
            bearish = True
            tradable = True
            description = "Developing bearish 1h trend with aligned momentum."

        # ----------------------------------------------------
        # Compression
        # ----------------------------------------------------

        elif (

            volatility.overall_regime == "LOW"

            and

            not volume.confirmed

        ):

            personality = "COMPRESSION"

            confidence = 85

            tradable = False

            description = (
                "Market is compressing. Breakout expected."
            )

        # ----------------------------------------------------
        # Explosive Breakout
        # ----------------------------------------------------

        elif (

            volatility.explosive

            and

            volume.confirmed

        ):

            personality = "BREAKOUT"

            confidence = 92

            tradable = True

            bullish = (
                trend.overall_direction == "BULLISH"
            )

            bearish = (
                trend.overall_direction == "BEARISH"
            )

            description = (
                "Explosive breakout in progress."
            )

        # ----------------------------------------------------
        # Trend Exhaustion
        # ----------------------------------------------------

        elif momentum.exhaustion:

            personality = "TREND_EXHAUSTION"

            confidence = 88

            tradable = False

            description = (
                "Momentum exhaustion detected."
            )

        # ----------------------------------------------------
        # High Volatility Chaos
        # ----------------------------------------------------

        elif (

            volatility.overall_regime == "HIGH"

            and

            not volume.confirmed

        ):

            personality = "CHAOTIC"

            confidence = 82

            tradable = False

            description = (
                "High volatility without confirmation."
            )

        return MarketPersonality(

            personality=personality,

            confidence=confidence,

            bullish=bullish,

            bearish=bearish,

            tradable=tradable,

            description=description,

        )
