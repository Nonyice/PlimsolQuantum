from decimal import Decimal

from app.extensions import db
from app.models.base import BaseModel


class SubscriptionPlan(BaseModel):

    __tablename__ = "subscription_plans"

    name = db.Column(
        db.String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    description = db.Column(
        db.Text,
        nullable=True,
    )

    price = db.Column(
        db.Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    duration_days = db.Column(
        db.Integer,
        nullable=False,
    )

    max_bots = db.Column(
        db.Integer,
        default=1,
        nullable=False,
    )

    max_exchanges = db.Column(
        db.Integer,
        default=1,
        nullable=False,
    )

    max_trading_pairs = db.Column(
        db.Integer,
        default=5,
        nullable=False,
    )

    paper_trading = db.Column(
        db.Boolean,
        default=True,
        nullable=False,
    )

    live_trading = db.Column(
        db.Boolean,
        default=False,
        nullable=False,
    )

    priority_support = db.Column(
        db.Boolean,
        default=False,
        nullable=False,
    )

    api_access = db.Column(
        db.Boolean,
        default=False,
        nullable=False,
    )

    is_trial = db.Column(
        db.Boolean,
        default=False,
        nullable=False,
    )

    subscriptions = db.relationship(
        "Subscription",
        back_populates="plan",
        lazy="select",
    )

    active = db.Column(
    db.Boolean,
    default=True,
    nullable=False,
    )

    def __repr__(self):
        return (
            f"<SubscriptionPlan("
            f"name='{self.name}', "
            f"price={self.price})>"
        )