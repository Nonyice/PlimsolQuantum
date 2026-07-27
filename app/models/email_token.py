from datetime import datetime, timedelta

from app.extensions import db
from app.models.base import BaseModel


class EmailToken(BaseModel):

    __tablename__ = "email_tokens"

    user_id = db.Column(
        db.ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    token = db.Column(
        db.String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    purpose = db.Column(
        db.String(50),
        nullable=False,
        index=True,
    )

    expires_at = db.Column(
        db.DateTime,
        default=lambda: datetime.utcnow() + timedelta(hours=1),
        nullable=False,
    )

    used = db.Column(
        db.Boolean,
        default=False,
        nullable=False,
    )

    used_at = db.Column(
        db.DateTime,
        nullable=True,
    )

    user = db.relationship(
        "User",
        back_populates="email_tokens",
        lazy="select",
    )

    @property
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at

    @property
    def is_valid(self) -> bool:
        return not self.used and not self.is_expired

    def mark_used(self):
        self.used = True
        self.used_at = datetime.utcnow()

    def __repr__(self):
        return (
            f"<EmailToken("
            f"user={self.user_id}, "
            f"purpose='{self.purpose}')>"
        )