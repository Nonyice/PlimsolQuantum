from datetime import datetime, timedelta

from app.extensions import db
from app.models.subscription import Subscription
from app.models.subscription_plan import SubscriptionPlan
from app.models.trial import Trial


class SubscriptionService:

    @staticmethod
    def create_trial(user):

        trial = Trial(
            user_id=user.id,
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=7),
        )

        db.session.add(trial)

        return trial

    @staticmethod
    def activate_plan(user, plan: SubscriptionPlan):

        subscription = Subscription(
            user_id=user.id,
            plan_id=plan.id,
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(
                days=plan.duration_days
            ),
            status="ACTIVE",
        )

        db.session.add(subscription)

        return subscription