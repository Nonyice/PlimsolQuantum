from app.extensions import db

from app.models.base import BaseModel


class Role(BaseModel):

    __tablename__ = "roles"

    name = db.Column(
        db.String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    description = db.Column(
        db.String(255),
        nullable=True,
    )

    users = db.relationship(
        "User",
        back_populates="role",
        lazy="select",
    )

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"<Role(name='{self.name}')>"