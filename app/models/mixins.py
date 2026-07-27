"""
Common mixins for SQLAlchemy models.
"""

from datetime import datetime

from app.extensions import db


class TimestampMixin:
    """Provides created and updated timestamps."""

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )


class StatusMixin:
    """Provides active/inactive status."""

    is_active = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )