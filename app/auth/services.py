from flask import (
    request,
    flash,
    redirect,
    url_for
)

from flask_login import login_user

from app.models.user import User

from app.repositories.user_repository import (
    UserRepository
)

from app.repositories.role_repository import (
    RoleRepository
)

from app.services.database_service import (
    DatabaseService
)


class AuthService:

    user_repo = UserRepository()

    role_repo = RoleRepository()

    @classmethod
    def register(cls):

        first_name = request.form.get(
            "first_name"
        )

        last_name = request.form.get(
            "last_name"
        )

        username = request.form.get(
            "username"
        )

        email = request.form.get(
            "email"
        )

        password = request.form.get(
            "password"
        )

        if cls.user_repo.exists_email(email):

            flash(
                "Email already exists.",
                "danger"
            )

            return redirect(
                url_for("auth.register")
            )

        role = cls.role_repo.get_by_name(
            "User"
        )

        user = User(

            first_name=first_name,

            last_name=last_name,

            username=username,

            email=email,

            role=role

        )

        user.set_password(password)

        DatabaseService.add(user)

        DatabaseService.commit()

        flash(
            "Registration successful.",
            "success"
        )

        return redirect(
            url_for("auth.login")
        )

    @classmethod
    def login(cls):

        email = request.form.get(
            "email"
        )

        password = request.form.get(
            "password"
        )

        user = cls.user_repo.find_by_email(
            email
        )

        if not user:

            flash(
                "Invalid credentials.",
                "danger"
            )

            return redirect(
                url_for("auth.login")
            )

        if not user.check_password(
            password
        ):

            flash(
                "Invalid credentials.",
                "danger"
            )

            return redirect(
                url_for("auth.login")
            )

        login_user(user)

        return redirect(
            url_for("dashboard.home")
        )