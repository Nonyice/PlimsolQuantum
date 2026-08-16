from __future__ import annotations

from datetime import datetime, timedelta

from app.extensions import db
from app.models.base import BaseModel


class Trial(BaseModel):
    __tablename__ = "trials"

    user_id = db.Column(
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    start_date = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    end_date = db.Column(
        db.DateTime,
        nullable=False,
    )

    paper_capital = db.Column(
        db.Numeric(18, 8),
        nullable=False,
        default=10000.0,
        server_default=db.text("10000"),
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="active",
        index=True,
    )

    converted_to_subscription = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        server_default=db.text("false"),
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default=db.func.now(),
    )

    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        server_default=db.func.now(),
    )

    user = db.relationship(
        "User",
        back_populates="trials",
        lazy="select",
    )

    @property
    def is_active(self) -> bool:
        if self.status != "active":
            return False

        if datetime.utcnow() >= self.end_date:
            return False

        return True

    @property
    def is_expired(self) -> bool:
        return (
            self.status == "expired"
            or datetime.utcnow() >= self.end_date
        )

    @property
    def days_remaining(self) -> int:
        if self.is_expired:
            return 0

        remaining = self.end_date - datetime.utcnow()

        return max(
            0,
            remaining.days + (
                1 if remaining.seconds > 0 else 0
            ),
        )

    def expire(self) -> None:
        self.status = "expired"

    @classmethod
    def create_trial(
        cls,
        user_id,
        days: int = 7,
        paper_capital: float = 10000.0,
    ) -> "Trial":
        if days <= 0:
            raise ValueError(
                "Trial duration must be greater than zero."
            )
        if paper_capital < 10 or paper_capital > 10000:
            raise ValueError("Trial paper capital must be between $10 and $10,000.")

        start = datetime.utcnow()
        end = start + timedelta(days=days)

        return cls(
            user_id=user_id,
            start_date=start,
            end_date=end,
            status="active",
            paper_capital=paper_capital,
            converted_to_subscription=False,
            created_at=start,
            updated_at=start,
        )

    def __repr__(self) -> str:
        return (
            f"<Trial("
            f"id={self.id}, "
            f"user_id={self.user_id}, "
            f"status='{self.status}', "
            f"converted_to_subscription="
            f"{self.converted_to_subscription}, "
            f"start_date='{self.start_date}', "
            f"end_date='{self.end_date}'"
            f")>"
        )