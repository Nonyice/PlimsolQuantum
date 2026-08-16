"""
Flask extensions.
"""

from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect


db = SQLAlchemy()

bcrypt = Bcrypt()

mail = Mail()

migrate = Migrate()

csrf = CSRFProtect()

login_manager = LoginManager()


def init_extensions(app):

    db.init_app(app)

    bcrypt.init_app(app)

    mail.init_app(app)

    migrate.init_app(app, db)

    csrf.init_app(app)

    login_manager.init_app(app)

    login_manager.login_view = "auth.login"

    login_manager.login_message_category = "warning"

    login_manager.session_protection = "strong"


@login_manager.user_loader
def load_user(user_id):

    from app.models.user import User

    return db.session.get(User, user_id)