from dataclasses import dataclass

from app.enums.market_type import MarketType


@dataclass(slots=True)
class Decision:

    action: str

    market: str

    position: str

    confidence: float

    leverage: int

    risk_percent: float

    stop_multiplier: float

    take_profit_rr: float

    should_execute: bool

    reason: str


class DecisionEngine:
    """
    Final intelligence layer.

    Converts the Opportunity into an executable
    trading decision.

    This engine NEVER analyses indicators.

    It only makes execution decisions.
    """

    def decide(

        self,

        opportunity,

        trend,

        momentum,

        volatility,

        personality,

        trading_account,

    ):

        # ------------------------------------
        # Reject poor opportunities
        # ------------------------------------

        if not opportunity.tradable:

            return Decision(

                action="NONE",

                market=trading_account.market_type.value,

                position="NONE",

                confidence=opportunity.probability,

                leverage=1,

                risk_percent=0,

                stop_multiplier=0,

                take_profit_rr=0,

                should_execute=False,

                reason=opportunity.reason,

            )

        # ------------------------------------
        # BUY / SELL
        # ------------------------------------

        if personality.bullish:

            action = "BUY"

            position = "LONG"

        elif personality.bearish:

            action = "SELL"

            position = "SHORT"

        else:

            return Decision(

                action="NONE",

                market=trading_account.market_type.value,

                position="NONE",

                confidence=50,

                leverage=1,

                risk_percent=0,

                stop_multiplier=0,

                take_profit_rr=0,

                should_execute=False,

                reason="No directional bias.",

            )

        # ------------------------------------
        # Spot Restriction
        # ------------------------------------

        if (

            trading_account.market_type

            == MarketType.SPOT

            and

            action == "SELL"

        ):

            return Decision(

                action="NONE",

                market="SPOT",

                position="NONE",

                confidence=0,

                leverage=1,

                risk_percent=0,

                stop_multiplier=0,

                take_profit_rr=0,

                should_execute=False,

                reason="Spot market cannot short.",

            )

        # ------------------------------------
        # Futures Leverage
        # ------------------------------------

        leverage = 1

        if trading_account.market_type == MarketType.FUTURES:

            if opportunity.score >= 95:

                leverage = 5

            elif opportunity.score >= 90:

                leverage = 4

            elif opportunity.score >= 85:

                leverage = 3

            else:

                leverage = 2

        # ------------------------------------
        # Risk %
        # ------------------------------------

        if opportunity.grade == "A+":

            risk = 2.0

        elif opportunity.grade == "A":

            risk = 1.5

        else:

            risk = 1.0

        # ------------------------------------
        # Take Profit
        # ------------------------------------

        if volatility.overall_regime == "HIGH":

            rr = 4.0

        elif volatility.overall_regime == "NORMAL":

            rr = 3.0

        else:

            rr = 2.0

        return Decision(

            action=action,

            market=trading_account.market_type.value,

            position=position,

            confidence=opportunity.probability,

            leverage=leverage,

            risk_percent=risk,

            stop_multiplier=volatility.recommended_stop_multiplier,

            take_profit_rr=rr,

            should_execute=True,

            reason=f"{opportunity.grade} setup approved.",

        )