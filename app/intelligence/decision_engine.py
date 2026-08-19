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
    Final PQI execution decision.

    CONFIDENCE IS THE PRIMARY EXECUTION GATE.

    At 60.1% confidence or higher, PQI is allowed to act provided a valid
    direction exists.

    The old opportunity.tradable gate is intentionally NOT checked here.

    Direction comes from OpportunityEngine:

        BULLISH -> BUY
        BEARISH -> SELL

    Spot rules:

        BUY  -> open/increase LONG
        SELL -> close existing LONG

    Futures rules:

        BUY  -> LONG
        SELL -> SHORT
    """

    MIN_EXECUTION_CONFIDENCE = 60.1

    def decide(
        self,
        opportunity,
        trend,
        momentum,
        volatility,
        personality,
        trading_account,
        existing_position=None,
    ):

        confidence = float(
            getattr(
                opportunity,
                "probability",
                0.0,
            )
            or 0.0
        )

        market_type = trading_account.market_type

        if not isinstance(
            market_type,
            MarketType,
        ):
            market_type = MarketType(
                str(market_type).lower()
            )

        # ============================================================
        # CONFIDENCE GATE
        # ============================================================
        #
        # This is intentionally the FIRST meaningful execution gate.
        #
        # 60.1% and above can execute.
        #

        if confidence < self.MIN_EXECUTION_CONFIDENCE:

            return self._none(
                market_type=market_type,
                confidence=confidence,
                reason=(
                    f"Confidence {confidence:.2f}% is below "
                    f"the {self.MIN_EXECUTION_CONFIDENCE:.1f}% "
                    "execution threshold."
                ),
            )

        # ============================================================
        # DIRECTION
        # ============================================================

        direction = str(
            getattr(
                opportunity,
                "direction",
                "",
            )
            or ""
        ).upper()

        # Compatibility fallback in case an older Opportunity object
        # has no direction field.

        if direction not in {
            "BULLISH",
            "BEARISH",
        }:

            if getattr(
                personality,
                "bullish",
                False,
            ):

                direction = "BULLISH"

            elif getattr(
                personality,
                "bearish",
                False,
            ):

                direction = "BEARISH"

        if direction == "BULLISH":

            action = "BUY"

            position = "LONG"

        elif direction == "BEARISH":

            action = "SELL"

            position = "SHORT"

        else:

            return self._none(
                market_type=market_type,
                confidence=confidence,
                reason=(
                    f"Confidence {confidence:.2f}% reached "
                    "the execution threshold, but no valid "
                    "BUY/SELL direction was produced."
                ),
            )

        # ============================================================
        # SPOT SELL
        # ============================================================
        #
        # Spot cannot create a SHORT.
        #
        # But SELL is absolutely valid when PQI already owns the asset.
        #
        # Therefore:
        #
        #   existing LONG -> SELL -> close LONG
        #
        # If there is no position, we cannot sell an asset we do not own.
        #

        if (
            market_type == MarketType.SPOT
            and action == "SELL"
        ):

            normalized_position = str(
                existing_position or ""
            ).upper()

            if normalized_position in {
                "LONG",
                "SPOT",
                "HOLDING",
                "ASSET",
            }:

                position = "LONG"

            else:

                return self._none(
                    market_type=market_type,
                    confidence=confidence,
                    reason=(
                        f"Confidence {confidence:.2f}% confirms "
                        "a bearish signal, but SPOT has no existing "
                        "LONG position/asset to sell."
                    ),
                )

        # ============================================================
        # FUTURES LEVERAGE
        # ============================================================

        leverage = 1

        if market_type == MarketType.FUTURES:

            score = float(
                getattr(
                    opportunity,
                    "score",
                    0.0,
                )
                or 0.0
            )

            if score >= 95:

                leverage = 5

            elif score >= 90:

                leverage = 4

            elif score >= 85:

                leverage = 3

            else:

                leverage = 2

        # ============================================================
        # RISK
        # ============================================================

        grade = str(
            getattr(
                opportunity,
                "grade",
                "",
            )
            or ""
        )

        if grade == "A+":

            risk = 2.0

        elif grade == "A":

            risk = 1.5

        else:

            risk = 1.0

        # ============================================================
        # TAKE PROFIT
        # ============================================================

        regime = getattr(
            volatility,
            "overall_regime",
            "NORMAL",
        )

        if regime == "HIGH":

            rr = 2.5

        elif regime == "NORMAL":

            rr = 2.0

        else:

            rr = 1.75

        # ============================================================
        # APPROVED
        # ============================================================

        if (
            market_type == MarketType.SPOT
            and action == "SELL"
        ):

            reason = (
                f"SELL approved: confidence "
                f"{confidence:.2f}% >= "
                f"{self.MIN_EXECUTION_CONFIDENCE:.1f}%; "
                "closing existing SPOT LONG."
            )

        else:

            reason = (
                f"{action} approved: confidence "
                f"{confidence:.2f}% >= "
                f"{self.MIN_EXECUTION_CONFIDENCE:.1f}%; "
                f"direction={direction}."
            )

        return Decision(

            action=action,

            market=market_type.value,

            position=position,

            confidence=confidence,

            leverage=leverage,

            risk_percent=risk,

            stop_multiplier=float(
                getattr(
                    volatility,
                    "recommended_stop_multiplier",
                    0,
                )
                or 0
            ),

            take_profit_rr=rr,

            should_execute=True,

            reason=reason,
        )

    # ================================================================
    # NONE DECISION
    # ================================================================

    @staticmethod
    def _none(
        market_type,
        confidence,
        reason,
    ):

        return Decision(

            action="NONE",

            market=market_type.value,

            position="NONE",

            confidence=confidence,

            leverage=1,

            risk_percent=0,

            stop_multiplier=0,

            take_profit_rr=0,

            should_execute=False,

            reason=reason,
        )