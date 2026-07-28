from sqlalchemy import func
from sqlalchemy import select

from app.extensions import db
from app.models.user import User


class UserRepository:

    @staticmethod
    def get_by_email(email: str):

        stmt = (
            select(User)
            .where(
                func.lower(User.email) == email.lower()
            )
        )

        return db.session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_by_username(username: str):

        stmt = (
            select(User)
            .where(User.username == username)
        )

        return db.session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def add(user: User):

        db.session.add(user)

    @staticmethod
    def flush():

        db.session.flush()