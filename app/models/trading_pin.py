from app.extensions import db
from app.extensions import bcrypt

from app.models.base import BaseModel


class TradingPin(BaseModel):

    __tablename__ = "trading_pins"

    user_id = db.Column(
        db.ForeignKey("users.id"),
        unique=True,
        nullable=False
    )

    pin_hash = db.Column(
        db.String(255),
        nullable=False
    )

    user = db.relationship("User")

    def set_pin(self, pin):

        self.pin_hash = bcrypt.generate_password_hash(
            pin
        ).decode()

    def verify_pin(self, pin):

        return bcrypt.check_password_hash(
            self.pin_hash,
            pin
        )