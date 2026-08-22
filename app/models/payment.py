from __future__ import annotations

from app.extensions import db
from app.models.base import BaseModel


class Payment(BaseModel):
    __tablename__ = "payments"

    user_id = db.Column(db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_id = db.Column(db.ForeignKey("subscription_plans.id", ondelete="RESTRICT"), nullable=False, index=True)
    subscription_id = db.Column(db.ForeignKey("subscriptions.id", ondelete="SET NULL"), nullable=True, index=True)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    currency = db.Column(db.String(3), nullable=False, default="USD")
    method = db.Column(db.String(30), nullable=False)  # PAYSTACK / BANK_TRANSFER
    status = db.Column(db.String(30), nullable=False, default="PENDING", index=True)
    reference = db.Column(db.String(120), unique=True, nullable=False, index=True)
    provider_reference = db.Column(db.String(120), nullable=True, index=True)
    evidence_path = db.Column(db.String(500), nullable=True)
    evidence_original_name = db.Column(db.String(255), nullable=True)
    rejection_reason = db.Column(db.Text, nullable=True)
    admin_notes = db.Column(db.Text, nullable=True)
    paid_at = db.Column(db.DateTime, nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    reviewed_by = db.Column(db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    user = db.relationship("User", foreign_keys=[user_id], back_populates="payments")
    reviewer = db.relationship("User", foreign_keys=[reviewed_by])
    plan = db.relationship("SubscriptionPlan", lazy="select")
    subscription = db.relationship("Subscription", back_populates="payments", lazy="select")
