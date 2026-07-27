"""
Base model for PlimsolQuantum.

All database models inherit from this class.
"""

from __future__ import annotations

import uuid

from datetime import datetime

from sqlalchemy.dialects.postgresql import UUID

from app.extensions import db


class BaseModel(db.Model):
    """
    Abstract base model.
    """

    __abstract__ = True

    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False
    )

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

    is_active = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )


    def __repr__(self):
        return f"<{self.__class__.__name__}>"