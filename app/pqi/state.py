from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class PQIState:
    session_id: str = ""
    status: str = "IDLE"
    exchange: str = ""
    exchange_id: str = ""
    market: str = ""
    active_market: str = ""
    market_type: str = "spot"
    symbol: str = ""
    mode: str = "trial"

    current_decision: str = "WAITING"
    confidence: float = 0.0
    market_regime: str = ""
    current_task: str = "Initializing"

    portfolio_value: float = 0.0
    starting_capital: float = 0.0
    available_capital: float = 0.0
    trading_capital: float = 0.0
    daily_pnl: float = 0.0
    realised_pnl: float = 0.0
    unrealised_pnl: float = 0.0
    open_positions: int = 0

    signals_analysed: int = 0
    trades_today: int = 0
    win_rate: float = 0.0
    risk_exposure: float = 0.0
    live_account_balance: float | None = None
    live_realised_pnl: float = 0.0

    last_price: float | None = None
    bid: float | None = None
    ask: float | None = None
    spread: float | None = None
    volume_24h: float | None = None
    high_24h: float | None = None
    low_24h: float | None = None
    change_24h: float | None = None
    change_percent_24h: float | None = None

    quote_currency: str = "USDT"
    base_currency: str = ""
    connection_status: str = "DISCONNECTED"
    exchange_connected: bool = False
    market_status: str = "OFFLINE"

    next_scan: datetime | None = None
    last_market_update: datetime | None = None
    intelligence: dict[str, Any] = field(default_factory=dict)
    candles: list[dict[str, Any]] = field(default_factory=list)
    candles_by_timeframe: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    markets: list[str] = field(default_factory=list)
    session_pairs: list[dict[str, Any]] = field(default_factory=list)
    paper_position: dict[str, Any] | None = None
    equity_curve: list[dict[str, Any]] = field(default_factory=list)
    execution_log: list[dict[str, Any]] = field(default_factory=list)
    activity: list[dict[str, Any]] = field(default_factory=list)


# Backwards compatibility for older imports. New multi-session code creates
# one PQIState per PQIEngine instance instead of sharing this object.
pqi_state = PQIState()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
