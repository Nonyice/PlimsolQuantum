from dataclasses import dataclass

from app.models.market_snapshot import MarketSnapshot


@dataclass(slots=True)
class AnalysisResult:
    """
    Complete output from the PQI Intelligence Core.

    This becomes the standard object passed
    throughout the system.
    """

    snapshot: MarketSnapshot

    trend: object

    momentum: object

    volume: object

    volatility: object

    support: object

    personality: object

    opportunity: object

    decision: object