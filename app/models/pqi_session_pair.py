from __future__ import annotations

from datetime import datetime

from sqlalchemy.dialects.postgresql import UUID
from app.extensions import db
from app.models.base import BaseModel


class PQISessionPair(BaseModel):
    __tablename__ = "pqi_session_pairs"

    session_id = db.Column(db.ForeignKey("pqi_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    symbol = db.Column(db.String(40), nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default="OBSERVING", index=True)
    side = db.Column(db.String(10), nullable=True)
    entry_price = db.Column(db.Numeric(30, 12), nullable=True)
    mark_price = db.Column(db.Numeric(30, 12), nullable=True)
    quantity = db.Column(db.Numeric(30, 12), nullable=True)
    notional = db.Column(db.Numeric(30, 12), nullable=True)
    stop_loss = db.Column(db.Numeric(30, 12), nullable=True)
    take_profit = db.Column(db.Numeric(30, 12), nullable=True)
    pnl = db.Column(db.Numeric(30, 12), nullable=False, default=0)
    opened_at = db.Column(db.DateTime, nullable=True)
    closed_at = db.Column(db.DateTime, nullable=True)
    last_update = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, server_default=db.func.now())

    session = db.relationship("PQISession", back_populates="pairs")
