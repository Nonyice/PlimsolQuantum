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