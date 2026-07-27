from app.extensions import db

from app.models.base import BaseModel


class Role(BaseModel):

    __tablename__ = "roles"

    name = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    description = db.Column(
        db.String(255)
    )

    users = db.relationship(
        "User",
        back_populates="role",
        lazy=True
    )

    def __str__(self):
        return self.name