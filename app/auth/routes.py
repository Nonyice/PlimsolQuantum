from app.auth import auth_bp

from app.controllers.auth_controller import (
    AuthController
)


@auth_bp.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    return AuthController.register()


@auth_bp.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    return AuthController.login()


@auth_bp.route("/logout")
def logout():

    return AuthController.logout()