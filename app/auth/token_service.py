"""
Email verification token service.
"""

import secrets

from datetime import datetime
from datetime import timedelta

from app.models.email_token import EmailToken


class TokenService:

    EXPIRY_HOURS = 1

    @classmethod
    def generate_token(cls):

        return secrets.token_urlsafe(48)

    @classmethod
    def create_email_token(
        cls,
        user
    ):

        token = EmailToken(

            user=user,

            token=cls.generate_token(),

            expires=datetime.utcnow()
            + timedelta(hours=cls.EXPIRY_HOURS)

        )

        return token

    @staticmethod
    def expired(email_token):

        return datetime.utcnow() > email_token.expires