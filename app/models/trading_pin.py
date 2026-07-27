from datetime import datetime

from app.extensions import bcrypt
from app.extensions import db
from app.models.base import BaseModel


class TradingPin(BaseModel):

    __tablename__ = "trading_pins"

    user_id = db.Column(
        db.ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        unique=True,
        index=True,
    )

    pin_hash = db.Column(
        db.String(255),
        nullable=False,
    )

    failed_attempts = db.Column(
        db.Integer,
        default=0,
        nullable=False,
    )

    locked_until = db.Column(
        db.DateTime,
        nullable=True,
    )

    last_used_at = db.Column(
        db.DateTime,
        nullable=True,
    )

    user = db.relationship(
        "User",
        back_populates="trading_pin",
        lazy="select",
    )

    def set_pin(self, pin: str) -> None:
        self.pin_hash = bcrypt.generate_password_hash(
            pin
        ).decode("utf-8")

    def check_pin(self, pin: str) -> bool:
        return bcrypt.check_password_hash(
            self.pin_hash,
            pin,
        )

    def record_success(self):
        self.failed_attempts = 0
        self.locked_until = None
        self.last_used_at = datetime.utcnow()

    def record_failure(self):
        self.failed_attempts += 1

    @property
    def is_locked(self) -> bool:
        return (
            self.locked_until is not None
            and datetime.utcnow() < self.locked_until
        )

    def __repr__(self):
        return (
            f"<TradingPin(user={self.user_id})>"
        )