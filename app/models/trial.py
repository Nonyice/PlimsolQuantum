from datetime import datetime, timedelta

from app.extensions import db
from app.models.base import BaseModel


class Trial(BaseModel):

    __tablename__ = "trials"

    user_id = db.Column(
        db.ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        unique=True,
        index=True,
    )

    start_date = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    end_date = db.Column(
        db.DateTime,
        default=lambda: datetime.utcnow() + timedelta(days=7),
        nullable=False,
    )

    converted_to_subscription = db.Column(
        db.Boolean,
        default=False,
        nullable=False,
    )

    user = db.relationship(
        "User",
        back_populates="trial",
        lazy="select",
    )

    @property
    def is_active(self) -> bool:
        return (
            datetime.utcnow() <= self.end_date
            and not self.converted_to_subscription
        )

    @property
    def days_remaining(self) -> int:
        remaining = (self.end_date - datetime.utcnow()).days
        return max(remaining, 0)

    def mark_as_converted(self):
        self.converted_to_subscription = True

    def __repr__(self):
        return (
            f"<Trial(user={self.user_id}, "
            f"expires='{self.end_date}')>"
        )