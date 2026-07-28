from app.extensions import db


class SubscriptionRepository:

    @staticmethod
    def add(subscription):

        db.session.add(subscription)