from flask import Flask

from config import config

from app.extensions import (
    db,
    migrate,
    login_manager,
    mail,
    bcrypt,
    csrf
)


def create_app(config_name="default"):

    app = Flask(__name__)

    app.config.from_object(config[config_name])

    db.init_app(app)

    migrate.init_app(app, db)

    login_manager.init_app(app)

    mail.init_app(app)

    bcrypt.init_app(app)

    csrf.init_app(app)

    login_manager.login_view = "auth.login"

    from app.auth.routes import auth_bp

    app.register_blueprint(auth_bp)

    return app