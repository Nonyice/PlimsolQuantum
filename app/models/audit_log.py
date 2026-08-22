from app.extensions import db
from app.models.base import BaseModel


class AuditLog(BaseModel):
    __tablename__ = "audit_logs"

    actor_id = db.Column(db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    target_user_id = db.Column(db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = db.Column(db.String(100), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    metadata_json = db.Column(db.Text, nullable=True)

    actor = db.relationship("User", foreign_keys=[actor_id])
    target_user = db.relationship("User", foreign_keys=[target_user_id])
