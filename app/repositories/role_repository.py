from app.models.role import Role

from app.repositories.base_repository import BaseRepository


class RoleRepository(BaseRepository):

    def __init__(self):

        super().__init__(Role)

    def get_by_name(self, name):

        return Role.query.filter_by(
            name=name
        ).first()