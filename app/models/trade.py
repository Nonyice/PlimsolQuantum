from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.extensions import db
from app.models.base import BaseModel

from app.enums.exchange import Exchange
from app.enums.market_type import MarketType
from app.enums.trade_side import TradeSide
from app.enums.trade_status import TradeStatus
from app.enums.position_type import PositionType


class Trade(BaseModel):
    __tablename__ = "trades"

    trade_reference = db.Column(
        UUID(as_uuid=True),
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        index=True,
    )

    user_id = db.Column(
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    trading_account_id = db.Column(
        db.ForeignKey("trading_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    exchange = db.Column(
        db.Enum(Exchange),
        nullable=False,
    )

    market_type = db.Column(
        db.Enum(MarketType),
        nullable=False,
    )

    symbol = db.Column(
        db.String(30),
        nullable=False,
        index=True,
    )

    timeframe = db.Column(
        db.String(10),
        nullable=False,
    )

    side = db.Column(
        db.Enum(TradeSide),
        nullable=False,
    )

    position = db.Column(
        db.Enum(PositionType),
        nullable=False,
    )

    leverage = db.Column(
        db.Integer,
        nullable=False,
        default=1,
    )

    risk_percent = db.Column(
        db.Numeric(5, 2),
        nullable=False,
    )

    entry_price = db.Column(
        db.Numeric(20, 10),
        nullable=False,
    )

    stop_loss = db.Column(
        db.Numeric(20, 10),
        nullable=False,
    )

    take_profit = db.Column(
        db.Numeric(20, 10),
        nullable=False,
    )

    quantity = db.Column(
        db.Numeric(20, 10),
        nullable=False,
    )

    status = db.Column(
        db.Enum(TradeStatus),
        nullable=False,
        default=TradeStatus.PENDING,
    )

    opened_at = db.Column(db.DateTime)

    closed_at = db.Column(db.DateTime)

    user = db.relationship(
        "User",
        back_populates="trades",
    )

    trading_account = db.relationship(
        "TradingAccount",
        back_populates="trades",
    )

    snapshot = db.relationship(
        "TradeSnapshot",
        back_populates="trade",
        uselist=False,
        cascade="all, delete-orphan",
    )

    outcome = db.relationship(
        "TradeOutcome",
        back_populates="trade",
        uselist=False,
        cascade="all, delete-orphan",
    )