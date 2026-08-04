from app.extensions import db
from app.models.base import BaseModel


class Position(BaseModel):

    __tablename__ = "positions"

    trading_account_id = db.Column(
        db.ForeignKey(
            "trading_accounts.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    symbol = db.Column(
        db.String(20),
        nullable=False,
    )

    side = db.Column(
        db.String(10),
        nullable=False,
    )

    quantity = db.Column(
        db.Float,
        nullable=False,
    )

    entry_price = db.Column(
        db.Float,
        nullable=False,
    )

    exit_price = db.Column(
        db.Float,
        nullable=True,
    )

    stop_loss = db.Column(
        db.Float,
        nullable=False,
    )

    take_profit = db.Column(
        db.Float,
        nullable=False,
    )

    status = db.Column(
        db.String(20),
        default="OPEN",
        nullable=False,
        index=True,
    )

    trading_account = db.relationship(
        "TradingAccount",
        backref="positions",
        lazy="select",
    )

    def __repr__(self):

        return (
            f"<Position("
            f"{self.symbol}, "
            f"{self.side}, "
            f"{self.status})>"
        )