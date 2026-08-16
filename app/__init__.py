from pathlib import Path

from flask import Flask, flash, redirect, request, url_for
from flask_wtf.csrf import CSRFError

from config import config

from app.extensions import init_extensions

from app.accounts import accounts_bp
from app.onboarding import onboarding_bp


BASE_DIR = Path(__file__).resolve().parent.parent


def create_app(config_name="development"):

    app = Flask(
        __name__,
        template_folder=BASE_DIR / "templates",
        static_folder=BASE_DIR / "static",
    )

    app.config.from_object(
        config[config_name]
    )

    init_extensions(app)

    @app.errorhandler(CSRFError)
    def handle_csrf_error(error):
        # Keep CSRF protection enabled. If an onboarding form is rejected,
        # return the user to the same step instead of exposing a raw 400 page.
        if request.path.startswith("/onboarding/"):
            flash(
                "Your security token has expired or is invalid. Please try again.",
                "danger",
            )
            return redirect(request.referrer or url_for("onboarding.profile"))

        return (
            f"CSRF Error: {error.description}",
            400,
        )

    from app.dashboard import dashboard_bp
    from app.auth import auth_bp
    from app.pqi.routes import pqi_bp

    app.register_blueprint(
        dashboard_bp
    )

    app.register_blueprint(
        auth_bp,
        url_prefix="/auth",
    )

    app.register_blueprint(
        pqi_bp
    )

    app.register_blueprint(
        accounts_bp
    )

    app.register_blueprint(
        onboarding_bp
    )

    return app