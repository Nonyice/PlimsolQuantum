from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy.dialects.postgresql import UUID

from app.extensions import db
from app.models.base import BaseModel


class PQISession(BaseModel):
    __tablename__ = "pqi_sessions"

    user_id = db.Column(
        db.ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    mode = db.Column(
        db.String(20),
        nullable=False,
        default="trial",
        index=True,
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="ACTIVE",
        index=True,
    )

    exchange = db.Column(
        db.String(30),
        nullable=False,
    )

    exchange_id = db.Column(
        db.String(100),
        nullable=True,
    )

    market_type = db.Column(
        db.String(20),
        nullable=False,
        default="spot",
    )

    capital = db.Column(
        db.Numeric(20, 8),
        nullable=False,
        default=1000,
    )

    started_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    last_heartbeat = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    stopped_at = db.Column(
        db.DateTime,
        nullable=True,
    )

    user = db.relationship(
        "User",
        back_populates="pqi_sessions",
        lazy="joined",
    )

    pairs = db.relationship(
        "PQISessionPair",
        back_populates="session",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="PQISessionPair.created_at.asc()",
    )