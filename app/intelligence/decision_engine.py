from dataclasses import dataclass

from app.intelligence.opportunity_engine import Opportunity


@dataclass
class Decision:
    action: str
    reason: str


class DecisionEngine:

    async def decide(self, opportunity: Opportunity) -> Decision:

        if not opportunity.available:
            return Decision(
                action="WAIT",
                reason=opportunity.reason
            )

        if opportunity.direction == "BULLISH":
            return Decision(
                action="BUY",
                reason=opportunity.reason
            )

        if opportunity.direction == "BEARISH":
            return Decision(
                action="SELL",
                reason=opportunity.reason
            )

        return Decision(
            action="WAIT",
            reason="No valid opportunity."
        )