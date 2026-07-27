from __future__ import annotations

from flask_login import UserMixin

from app.extensions import db
from app.extensions import bcrypt
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
        default=False
    )

    two_factor_enabled = db.Column(
        db.Boolean,
        default=False
    )

    role_id = db.Column(
        db.ForeignKey("roles.id"),
        nullable=False
    )

    role = db.relationship(
        "Role",
        back_populates="users"
    )

    def set_password(self, password):

        self.password_hash = bcrypt.generate_password_hash(
            password
        ).decode("utf-8")

    def check_password(self, password):

        return bcrypt.check_password_hash(
            self.password_hash,
            password
        )

    @property
    def is_admin(self):

        return self.role.name.lower() == "admin"

    def get_id(self):

        return str(self.id)

    def __repr__(self):

        return f"<User {self.username}>"