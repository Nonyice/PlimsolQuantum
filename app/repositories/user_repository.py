from app.models.user import User

from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository):

    def __init__(self):

        super().__init__(User)

    def find_by_email(self, email):

        return User.query.filter_by(
            email=email
        ).first()

    def find_by_username(self, username):

        return User.query.filter_by(
            username=username
        ).first()

    def exists_email(self, email):

        return self.find_by_email(email) is not None

    def exists_username(self, username):

        return self.find_by_username(username) is not None