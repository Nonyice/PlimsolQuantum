from app.auth import auth_bp

from app.controllers.auth_controller import AuthController


@auth_bp.route(
    "/register",
    methods=["GET", "POST"],
)
def register():
    return AuthController.register()


@auth_bp.route(
    "/login",
    methods=["GET", "POST"],
)
def login():
    return AuthController.login()


@auth_bp.route("/logout")
def logout():
    return AuthController.logout()


@auth_bp.route(
    "/forgot-password",
    methods=["GET", "POST"],
)
def forgot_password():
    return AuthController.forgot_password()


@auth_bp.route(
    "/reset-password/<token>",
    methods=["GET", "POST"],
)
def reset_password(token):
    return AuthController.reset_password(token)


@auth_bp.route(
    "/verify-email/<token>",
)
def verify_email(token):
    return AuthController.verify_email(token)


@auth_bp.route(
    "/resend-verification",
    methods=["GET", "POST"],
)
def resend_verification():
    return AuthController.resend_verification()