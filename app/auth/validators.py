"""
Authentication validators.
"""

import re

from app.repositories.user_repository import UserRepository


class AuthValidator:

    user_repo = UserRepository()

    @classmethod
    def validate_registration(
        cls,
        first_name,
        last_name,
        username,
        email,
        password,
        confirm_password
    ):

        errors = []

        if not first_name.strip():
            errors.append("First name is required.")

        if not last_name.strip():
            errors.append("Last name is required.")

        if len(username) < 4:
            errors.append("Username must be at least 4 characters.")

        if cls.user_repo.exists_username(username):
            errors.append("Username already exists.")

        if cls.user_repo.exists_email(email):
            errors.append("Email already exists.")

        email_pattern = (
            r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
        )

        if not re.match(email_pattern, email):
            errors.append("Invalid email address.")

        if len(password) < 8:
            errors.append(
                "Password must be at least 8 characters."
            )

        if password != confirm_password:
            errors.append(
                "Passwords do not match."
            )

        return errors