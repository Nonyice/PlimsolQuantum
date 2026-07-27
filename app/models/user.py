from __future__ import annotations

from flask_login import UserMixin

from app.extensions import bcrypt
from app.extensions import db

from app.models.base import BaseModel


class User(UserMixin, BaseModel):

    __tablename__ = "users"

    first_name = db.Column(
        db.String(100),
        nullable=False
    )

    last_name = db.Column(
        db.String(100),
        nullable=False
    )

    username = db.Column(
        db.String(80),
        unique=True,
        nullable=False,
        index=True
    )

    email = db.Column(
        db.String(150),
        unique=True,
        nullable=False,
        index=True
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    email_verified = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    two_factor_enabled = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    role_id = db.Column(
        db.ForeignKey("roles.id"),
        nullable=False
    )

    role = db.relationship(
        "Role",
        back_populates="users"
    )

    subscriptions = db.relationship(
        "Subscription",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    trial = db.relationship(
        "Trial",
        uselist=False,
        back_populates="user",
        cascade="all, delete-orphan"
    )

    trading_pin = db.relationship(
        "TradingPin",
        uselist=False,
        back_populates="user",
        cascade="all, delete-orphan"
    )

    email_tokens = db.relationship(
        "EmailToken",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    activity_logs = db.relationship(
        "ActivityLog",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def set_password(self, password: str) -> None:
        self.password_hash = bcrypt.generate_password_hash(
            password
        ).decode("utf-8")

    def check_password(self, password: str) -> bool:
        return bcrypt.check_password_hash(
            self.password_hash,
            password
        )

    @property
    def is_admin(self):
        return self.role.name.lower() == "admin"

    def get_id(self):
        return str(self.id)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return f"<User {self.username}>"