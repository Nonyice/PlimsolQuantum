from dataclasses import dataclass

from app.intelligence.observer import MarketSnapshot


@dataclass
class Opportunity:
    available: bool
    score: float
    direction: str
    reason: str


class OpportunityEngine:
    """
    Determines whether PQI should consider trading.
    """

    async def evaluate(self, snapshot: MarketSnapshot) -> Opportunity:

        if not snapshot.healthy:
            return Opportunity(
                available=False,
                score=0.0,
                direction="WAIT",
                reason="Market conditions are unhealthy."
            )

        return Opportunity(
            available=True,
            score=snapshot.confidence,
            direction=snapshot.trend,
            reason="Opportunity detected."
        )