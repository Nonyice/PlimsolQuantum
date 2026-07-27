from app.extensions import db
from app.models.base import BaseModel


class SubscriptionPlan(BaseModel):

    __tablename__ = "subscription_plans"

    name = db.Column(db.String(50), unique=True, nullable=False)

    price = db.Column(db.Numeric(10, 2), nullable=False)

    duration_days = db.Column(db.Integer, nullable=False)

    max_bots = db.Column(db.Integer, default=1)

    max_exchanges = db.Column(db.Integer, default=1)

    paper_trading = db.Column(db.Boolean, default=True)

    live_trading = db.Column(db.Boolean, default=False)

    description = db.Column(db.Text)

    subscriptions = db.relationship(
        "Subscription",
        back_populates="plan",
        lazy=True
    )

    def __repr__(self):
        return f"<SubscriptionPlan {self.name}>"