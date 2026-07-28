from sqlalchemy import select

from app.extensions import db
from app.models.role import Role


class RoleRepository:

    @staticmethod
    def get_by_name(name: str):

        stmt = select(Role).where(Role.name == name)

        return db.session.execute(stmt).scalar_one_or_none()