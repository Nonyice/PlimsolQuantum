import secrets

from datetime import datetime
from datetime import timedelta

from app.extensions import db

from app.models.base import BaseModel


class EmailToken(BaseModel):

    __tablename__ = "email_tokens"

    user_id = db.Column(
        db.ForeignKey("users.id"),
        nullable=False
    )

    token = db.Column(
        db.String(128),
        default=lambda: secrets.token_urlsafe(32),
        unique=True
    )

    expires = db.Column(
        db.DateTime,
        default=lambda: datetime.utcnow() + timedelta(hours=1)
    )

    used = db.Column(
        db.Boolean,
        default=False
    )

    user = db.relationship(
    "User",
    back_populates="email_tokens"
)