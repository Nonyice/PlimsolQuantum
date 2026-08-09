from flask import (
    render_template,
    redirect,
    url_for,
    request,
)

from flask_login import (
    current_user,
)

from app.auth.forms import (
    RegistrationForm,
    LoginForm,
    ForgotPasswordForm,
    ResetPasswordForm,
    ResendVerificationForm,
)

from app.auth.services import AuthService


class AuthController:

    @staticmethod
    def register():
        form = RegistrationForm()

        if request.method == "GET":
            return render_template(
                "auth/register.html",
                form=form,
            )

        return AuthService.register()

    @staticmethod
    def login():
        form = LoginForm()

        if request.method == "GET":
            return render_template(
                "auth/login.html",
                form=form,
            )

        response = AuthService.login()

        return response

    @staticmethod
    def logout():
        return AuthService.logout()

    @staticmethod
    def forgot_password():
        form = ForgotPasswordForm()

        if request.method == "GET":
            return render_template(
                "auth/forgot_password.html",
                form=form,
            )

        return AuthService.forgot_password()

    @staticmethod
    def reset_password(token):
        form = ResetPasswordForm()

        if request.method == "GET":
            return render_template(
                "auth/reset_password.html",
                form=form,
                token=token,
            )

        return AuthService.reset_password(token)

    @staticmethod
    def verify_email(token):
        return AuthService.verify_email(token)

    @staticmethod
    def resend_verification():
        form = ResendVerificationForm()

        if request.method == "GET":
            return render_template(
                "auth/resend_verification.html",
                form=form,
            )

        return AuthService.resend_verification()