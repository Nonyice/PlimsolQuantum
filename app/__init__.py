from flask import Flask

from config import config

from app.extensions import init_extensions


def create_app(config_name="development"):

    app = Flask(__name__)

    app.config.from_object(config[config_name])

    init_extensions(app)

    # Blueprints
    from app.auth import auth_bp

    app.register_blueprint(auth_bp)

    return app