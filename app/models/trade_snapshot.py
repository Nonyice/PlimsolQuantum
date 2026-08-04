from app.extensions import db
from app.models.base import BaseModel


class TradeSnapshot(BaseModel):
    __tablename__ = "trade_snapshots"

    trade_id = db.Column(
        db.ForeignKey(
            "trades.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        unique=True,
        index=True,
    )

    market_snapshot = db.Column(
        db.JSON,
        nullable=False,
    )

    analysis = db.Column(
        db.JSON,
        nullable=False,
    )

    decision = db.Column(
        db.JSON,
        nullable=False,
    )

    trade = db.relationship(
        "Trade",
        back_populates="snapshot",
    )