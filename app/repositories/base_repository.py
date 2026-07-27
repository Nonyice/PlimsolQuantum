"""
Base Repository.

Provides common CRUD operations.
"""

from app.extensions import db


class BaseRepository:

    model = None

    def __init__(self, model):

        self.model = model

    def add(self, entity):

        db.session.add(entity)

    def delete(self, entity):

        db.session.delete(entity)

    def get(self, entity_id):

        return self.model.query.get(entity_id)

    def all(self):

        return self.model.query.all()

    def commit(self):

        db.session.commit()

    def rollback(self):

        db.session.rollback()

    def flush(self):

        db.session.flush()