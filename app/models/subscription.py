from datetime import datetime

from app.extensions import db
from app.models.base import BaseModel


class Subscription(BaseModel):

    __tablename__ = "subscriptions"

    user_id = db.Column(
        db.ForeignKey("users.id"),
        nullable=False
    )

    plan_id = db.Column(
        db.ForeignKey("subscription_plans.id"),
        nullable=False
    )

    start_date = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    end_date = db.Column(db.DateTime)

    active = db.Column(
        db.Boolean,
        default=True
    )

    user = db.relationship(
    "User",
    back_populates="subscriptions"
)

    plan = db.relationship(
        "SubscriptionPlan",
        back_populates="subscriptions"
    )