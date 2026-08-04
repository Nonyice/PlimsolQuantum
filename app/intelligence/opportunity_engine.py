from dataclasses import dataclass


@dataclass(slots=True)
class Opportunity:

    score: float

    grade: str

    probability: float

    tradable: bool

    reason: str

    expected_reward: float

    expected_risk: float


class OpportunityEngine:
    """
    Determines whether a setup is worth trading.

    Inputs:

    - Trend
    - Momentum
    - Volume
    - Volatility
    - Support
    - Market Personality
    """

    TREND_WEIGHT = 25

    MOMENTUM_WEIGHT = 20

    VOLUME_WEIGHT = 15

    VOLATILITY_WEIGHT = 10

    SUPPORT_WEIGHT = 15

    PERSONALITY_WEIGHT = 15

    def evaluate(

        self,

        trend,

        momentum,

        volume,

        volatility,

        support,

        personality,

    ):

        score = 0

        # ----------------------------------------
        # Trend
        # ----------------------------------------

        score += (

            trend.alignment_score

            * self.TREND_WEIGHT

        )

        # ----------------------------------------
        # Momentum
        # ----------------------------------------

        score += (

            momentum.confidence / 100

        ) * self.MOMENTUM_WEIGHT

        # ----------------------------------------
        # Volume
        # ----------------------------------------

        if volume.confirmed:

            score += self.VOLUME_WEIGHT

        else:

            score += self.VOLUME_WEIGHT * 0.25

        # ----------------------------------------
        # Volatility
        # ----------------------------------------

        if volatility.overall_regime == "NORMAL":

            score += self.VOLATILITY_WEIGHT

        elif volatility.overall_regime == "LOW":

            score += self.VOLATILITY_WEIGHT * 0.70

        else:

            score += self.VOLATILITY_WEIGHT * 0.40

        # ----------------------------------------
        # Support / Resistance
        # ----------------------------------------

        if support.market_location == "AT_SUPPORT":

            score += self.SUPPORT_WEIGHT

        elif support.market_location == "MIDDLE":

            score += self.SUPPORT_WEIGHT * 0.50

        # ----------------------------------------
        # Market Personality
        # ----------------------------------------

        if personality.tradable:

            score += (

                personality.confidence / 100

            ) * self.PERSONALITY_WEIGHT

        score = round(score, 2)

        probability = score

        # ----------------------------------------
        # Trade Grade
        # ----------------------------------------

        if score >= 95:

            grade = "A+"

        elif score >= 90:

            grade = "A"

        elif score >= 80:

            grade = "B"

        elif score >= 70:

            grade = "C"

        else:

            grade = "REJECT"

        tradable = score >= 80

        if tradable:

            reason = (

                f"{grade} quality opportunity."

            )

        else:

            reason = (

                "Opportunity quality is below threshold."

            )

        expected_reward = round(

            1.5 + (score / 20),

            2,

        )

        expected_risk = round(

            max(

                1,

                6 - expected_reward,

            ),

            2,

        )

        return Opportunity(

            score=score,

            grade=grade,

            probability=probability,

            tradable=tradable,

            reason=reason,

            expected_reward=expected_reward,

            expected_risk=expected_risk,

        )