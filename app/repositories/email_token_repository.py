from sqlalchemy import select

from app.extensions import db
from app.models.email_token import EmailToken


class EmailTokenRepository:

    @staticmethod
    def create(token):

        db.session.add(token)

    @staticmethod
    def get(token_value):

        stmt = (
            select(EmailToken)
            .where(
                EmailToken.token == token_value
            )
        )

        return db.session.execute(stmt).scalar_one_or_none()