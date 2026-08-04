from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class PQIState:

    status: str = "IDLE"

    exchange: str = ""

    market: str = ""

    current_decision: str = "WAITING"

    confidence: float = 0.0

    market_regime: str = ""

    current_task: str = "Initializing"

    portfolio_value: float = 0.0

    daily_pnl: float = 0.0

    open_positions: int = 0

    signals_analysed: int = 0

    trades_today: int = 0

    win_rate: float = 0.0

    risk_exposure: float = 0.0

    next_scan: datetime | None = None


pqi_state = PQIState()