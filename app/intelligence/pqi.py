from app.intelligence.observer import MarketObserver
from app.intelligence.trend_engine import TrendEngine
from app.intelligence.momentum_engine import MomentumEngine
from app.intelligence.volume_engine import VolumeEngine
from app.intelligence.volatility_engine import VolatilityEngine
from app.intelligence.support_resistance_engine import SupportResistanceEngine
from app.intelligence.market_personality_engine import MarketPersonalityEngine
from app.intelligence.opportunity_engine import OpportunityEngine
from app.intelligence.decision_engine import DecisionEngine


class PQI:
    """Single intelligence pipeline shared by trial and live execution."""

    def __init__(self):
        self.observer = MarketObserver()
        self.trend = TrendEngine()
        self.momentum = MomentumEngine()
        self.volume = VolumeEngine()
        self.volatility = VolatilityEngine()
        self.support = SupportResistanceEngine()
        self.personality = MarketPersonalityEngine()
        self.opportunity = OpportunityEngine()
        self.decision = DecisionEngine()

    async def observe(self, trading_account, symbol=None):
        return await self.observer.observe(trading_account, symbol=symbol)

    async def analyse(self, snapshot, trading_account, account_balance):
        trend = self.trend.analyse(snapshot)
        momentum = self.momentum.analyse(snapshot)
        volume = self.volume.analyse(snapshot)
        volatility = self.volatility.analyse(snapshot)
        support = self.support.analyse(snapshot)
        personality = self.personality.analyse(trend, momentum, volume, volatility, support)
        opportunity = self.opportunity.evaluate(trend, momentum, volume, volatility, support, personality)
        decision = self.decision.decide(opportunity, trend, momentum, volatility, personality, trading_account)
        return {
            "snapshot": snapshot,
            "trend": trend,
            "momentum": momentum,
            "volume": volume,
            "volatility": volatility,
            "support": support,
            "personality": personality,
            "opportunity": opportunity,
            "decision": decision,
        }
