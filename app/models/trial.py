from datetime import datetime
from datetime import timedelta

from app.extensions import db
from app.models.base import BaseModel


class Trial(BaseModel):

    __tablename__ = "trials"

    user_id = db.Column(
        db.ForeignKey("users.id"),
        nullable=False
    )

    started = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    expires = db.Column(
        db.DateTime,
        default=lambda: datetime.utcnow() + timedelta(days=7)
    )

    active = db.Column(
        db.Boolean,
        default=True
    )

    user = db.relationship(
    "User",
    back_populates="trial"
)