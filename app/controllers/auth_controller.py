from flask import (
    render_template,
    redirect,
    url_for,
    flash,
    request
)

from flask_login import (
    login_user,
    logout_user,
    login_required
)

from app.auth.services import AuthService


class AuthController:

    @staticmethod
    def register():

        if request.method == "GET":

            return render_template(
                "auth/register.html"
            )

        return AuthService.register()

    @staticmethod
    def login():

        if request.method == "GET":

            return render_template(
                "auth/login.html"
            )

        return AuthService.login()

    @staticmethod
    @login_required
    def logout():

        logout_user()

        flash(
            "Logged out successfully.",
            "success"
        )

        return redirect(
            url_for("auth.login")
        )