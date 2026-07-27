"""
Common mixins for SQLAlchemy models.
"""

from datetime import datetime

from app.extensions import db


class TimestampMixin:
    """Provides timestamp fields."""

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    deleted_at = db.Column(
        db.DateTime,
        nullable=True,
    )


class StatusMixin:
    """Provides active/inactive status."""

    is_active = db.Column(
        db.Boolean,
        default=True,
        nullable=False,
    )