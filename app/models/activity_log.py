from app.extensions import db
from app.models.base import BaseModel


class ActivityLog(BaseModel):

    __tablename__ = "activity_logs"

    user_id = db.Column(
        db.ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    action = db.Column(
        db.String(100),
        nullable=False,
        index=True,
    )

    description = db.Column(
        db.Text,
        nullable=True,
    )

    endpoint = db.Column(
        db.String(255),
        nullable=True,
    )

    request_method = db.Column(
        db.String(10),
        nullable=True,
    )

    ip_address = db.Column(
        db.String(45),
        nullable=True,
    )

    user_agent = db.Column(
        db.Text,
        nullable=True,
    )

    status = db.Column(
        db.String(20),
        default="SUCCESS",
        nullable=False,
        index=True,
    )

    user = db.relationship(
        "User",
        back_populates="activity_logs",
        lazy="select",
    )

    def __repr__(self):
        return (
            f"<ActivityLog("
            f"user={self.user_id}, "
            f"action='{self.action}', "
            f"status='{self.status}')>"
        )