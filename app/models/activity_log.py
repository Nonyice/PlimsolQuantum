from app.extensions import db
from app.models.base import BaseModel


class ActivityLog(BaseModel):

    __tablename__ = "activity_logs"

    user_id = db.Column(
        db.ForeignKey("users.id")
    )

    action = db.Column(
        db.String(255),
        nullable=False
    )

    ip_address = db.Column(
        db.String(80)
    )

    user_agent = db.Column(
        db.Text
    )

    user = db.relationship(
    "User",
    back_populates="activity_logs"
)