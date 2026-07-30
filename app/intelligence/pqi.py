from app.intelligence.observer import MarketObserver
from app.intelligence.opportunity_engine import OpportunityEngine
from app.intelligence.decision_engine import DecisionEngine
from app.intelligence.risk_guardian import RiskGuardian
from app.intelligence.profit_harvester import ProfitHarvester


class PQI:

    def __init__(self):

        self.observer = MarketObserver()
        self.opportunity = OpportunityEngine()
        self.decision = DecisionEngine()
        self.risk = RiskGuardian()
        self.harvester = ProfitHarvester()

    async def think(self, trading_account):

        snapshot = await self.observer.observe(trading_account)

        opportunity = await self.opportunity.evaluate(snapshot)

        decision = await self.decision.decide(opportunity)

        approved = await self.risk.approve(
            trading_account,
            decision
        )

        return {
            "snapshot": snapshot,
            "opportunity": opportunity,
            "decision": decision,
            "approved": approved
        }