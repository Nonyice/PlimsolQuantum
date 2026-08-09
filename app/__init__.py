from pathlib import Path

from flask import Flask
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