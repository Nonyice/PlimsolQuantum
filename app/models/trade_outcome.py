from app.extensions import db
from app.models.base import BaseModel

from app.enums.exit_reason import ExitReason


class TradeOutcome(BaseModel):
    __tablename__ = "trade_outcomes"

    trade_id = db.Column(
        db.ForeignKey(
            "trades.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        unique=True,
        index=True,
    )

    exit_price = db.Column(
        db.Numeric(20, 10),
        nullable=False,
    )

    gross_profit = db.Column(
        db.Numeric(20, 10),
        nullable=False,
        default=0,
    )

    net_profit = db.Column(
        db.Numeric(20, 10),
        nullable=False,
        default=0,
    )

    fees = db.Column(
        db.Numeric(20, 10),
        nullable=False,
        default=0,
    )

    slippage = db.Column(
        db.Numeric(20, 10),
        nullable=False,
        default=0,
    )

    reward_risk = db.Column(
        db.Numeric(10, 4),
        nullable=False,
        default=0,
    )

    drawdown = db.Column(
        db.Numeric(10, 4),
        nullable=False,
        default=0,
    )

    duration_minutes = db.Column(
        db.Integer,
        nullable=False,
        default=0,
    )

    win = db.Column(
        db.Boolean,
        nullable=False,
    )

    exit_reason = db.Column(
        db.Enum(ExitReason),
        nullable=False,
    )

    closed_at = db.Column(
        db.DateTime,
        nullable=False,
    )

    trade = db.relationship(
        "Trade",
        back_populates="outcome",
    )