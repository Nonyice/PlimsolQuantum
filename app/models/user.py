from __future__ import annotations

from datetime import datetime

from flask_login import UserMixin

from app.extensions import bcrypt
from app.extensions import db
from app.models.base import BaseModel


class User(UserMixin, BaseModel):

    __tablename__ = "users"

    first_name = db.Column(
        db.String(100),
        nullable=False,
    )

    last_name = db.Column(
        db.String(100),
        nullable=False,
    )

    username = db.Column(
        db.String(80),
        unique=True,
        nullable=False,
        index=True,
    )

    email = db.Column(
        db.String(150),
        unique=True,
        nullable=False,
        index=True,
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False,
    )

    email_verified = db.Column(
        db.Boolean,
        default=False,
        nullable=False,
    )

    email_verified_at = db.Column(
        db.DateTime,
        nullable=True,
    )

    two_factor_enabled = db.Column(
        db.Boolean,
        default=False,
        nullable=False,
    )

    last_login = db.Column(
        db.DateTime,
        nullable=True,
    )

    failed_login_attempts = db.Column(
        db.Integer,
        default=0,
        nullable=False,
    )

    locked_until = db.Column(
        db.DateTime,
        nullable=True,
    )

    timezone = db.Column(
        db.String(50),
        default="UTC",
        nullable=False,
    )

    country = db.Column(
        db.String(100),
        nullable=True,
    )

    role_id = db.Column(
        db.ForeignKey(
            "roles.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    role = db.relationship(
        "Role",
        back_populates="users",
        lazy="select",
    )

    subscriptions = db.relationship(
        "Subscription",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    trial = db.relationship(
        "Trial",
        uselist=False,
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    trading_pin = db.relationship(
        "TradingPin",
        uselist=False,
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    email_tokens = db.relationship(
        "EmailToken",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    activity_logs = db.relationship(
        "ActivityLog",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def set_password(self, password: str) -> None:
        self.password_hash = bcrypt.generate_password_hash(
            password
        ).decode("utf-8")

    def check_password(self, password: str) -> bool:
        return bcrypt.check_password_hash(
            self.password_hash,
            password,
        )

    @property
    def is_admin(self) -> bool:
        return self.role is not None and self.role.name.lower() == "admin"

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    def get_id(self) -> str:
        return str(self.id)

    def record_successful_login(self):
        self.last_login = datetime.utcnow()
        self.failed_login_attempts = 0
        self.locked_until = None

    def record_failed_login(self):
        self.failed_login_attempts += 1

    def __repr__(self):
        return f"<User(username='{self.username}', email='{self.email}')>"