"""
Base model for PlimsolQuantum.

All models inherit from this class.
"""

from __future__ import annotations

import uuid

from sqlalchemy.dialects.postgresql import UUID

from app.extensions import db
from app.models.mixins import TimestampMixin
from app.models.mixins import StatusMixin


class BaseModel(
    TimestampMixin,
    StatusMixin,
    db.Model
):
    __abstract__ = True

    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False
    )

    def __repr__(self):
        return f"<{self.__class__.__name__}>"