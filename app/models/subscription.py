from datetime import datetime

from app.extensions import db
from app.models.base import BaseModel


class Subscription(BaseModel):

    __tablename__ = "subscriptions"

    user_id = db.Column(
        db.ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    plan_id = db.Column(
        db.ForeignKey(
            "subscription_plans.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    start_date = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    end_date = db.Column(
        db.DateTime,
        nullable=False,
    )

    status = db.Column(
        db.String(20),
        default="ACTIVE",
        nullable=False,
        index=True,
    )

    auto_renew = db.Column(
        db.Boolean,
        default=False,
        nullable=False,
    )

    cancelled_at = db.Column(
        db.DateTime,
        nullable=True,
    )

    user = db.relationship(
        "User",
        back_populates="subscriptions",
        lazy="select",
    )

    plan = db.relationship(
        "SubscriptionPlan",
        back_populates="subscriptions",
        lazy="select",
    )

    @property
    def is_active(self) -> bool:
        return (
            self.status == "ACTIVE"
            and datetime.utcnow() <= self.end_date
        )

    @property
    def days_remaining(self) -> int:
        remaining = (self.end_date - datetime.utcnow()).days
        return max(remaining, 0)

    def cancel(self):
        self.status = "CANCELLED"
        self.cancelled_at = datetime.utcnow()

    def expire(self):
        self.status = "EXPIRED"

    def __repr__(self):
        return (
            f"<Subscription("
            f"user={self.user_id}, "
            f"plan={self.plan_id}, "
            f"status='{self.status}')>"
        )