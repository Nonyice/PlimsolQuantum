"""
Centralised transaction manager.
"""

from app.extensions import db


class DatabaseService:

    @staticmethod
    def commit():

        db.session.commit()

    @staticmethod
    def rollback():

        db.session.rollback()

    @staticmethod
    def flush():

        db.session.flush()

    @staticmethod
    def add(entity):

        db.session.add(entity)

    @staticmethod
    def delete(entity):

        db.session.delete(entity)