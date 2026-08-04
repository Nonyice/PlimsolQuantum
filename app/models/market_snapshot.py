from dataclasses import dataclass, field
from typing import Any

from app.intelligence.indicator_service import IndicatorSet


@dataclass(slots=True)
class TimeframeData:

    timeframe: str

    candles: list

    indicators: IndicatorSet | None = None


@dataclass(slots=True)
class MarketSnapshot:

    symbol: str

    exchange: str

    timeframes: dict[str, TimeframeData] = field(default_factory=dict)

    ticker: dict[str, Any] | None = None

    order_book: dict[str, Any] | None = None

    trades: list | None = None

    exchange_info: dict[str, Any] | None = None

    funding_rate: dict[str, Any] | None = None

    open_interest: dict[str, Any] | None = None

    server_time: int | None = None