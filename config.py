"""
Application configuration for PlimsolQuantum.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")


class Config:

    APP_NAME = os.getenv(
        "APP_NAME",
        "PlimsolQuantum",
    )

    APP_VERSION = os.getenv(
        "APP_VERSION",
        "1.0.0",
    )

    COMPANY_NAME = os.getenv(
        "COMPANY_NAME",
        "PlimsolTech",
    )

    SECRET_KEY = os.getenv("SECRET_KEY")

    SECURITY_PASSWORD_SALT = os.getenv(
        "SECURITY_PASSWORD_SALT"
    )

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    # ======================================================
    # APPLICATION BASE URL
    # ======================================================

    APP_BASE_URL = os.getenv(
        "APP_BASE_URL"
    )

    # ======================================================
    # MAIL
    # ======================================================

    MAIL_SERVER = os.getenv(
        "MAIL_SERVER"
    )

    MAIL_PORT = int(
        os.getenv(
            "MAIL_PORT",
            587,
        )
    )

    MAIL_USE_TLS = (
        os.getenv(
            "MAIL_USE_TLS",
            "True",
        ).lower()
        == "true"
    )

    MAIL_USE_SSL = False

    MAIL_USERNAME = os.getenv(
        "MAIL_USERNAME"
    )

    MAIL_PASSWORD = os.getenv(
        "MAIL_PASSWORD"
    )

    MAIL_DEFAULT_SENDER = os.getenv(
        "MAIL_DEFAULT_SENDER"
    )

    # ======================================================
    # SESSION
    # ======================================================

    REMEMBER_COOKIE_DURATION = 7 * 24 * 60 * 60

    SESSION_COOKIE_HTTPONLY = True

    SESSION_COOKIE_SAMESITE = "Lax"

    # Flask-WTF CSRF protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_CHECK_DEFAULT = True
    # Do not let a user lose a valid onboarding form simply because
    # the page has been open for a while.
    WTF_CSRF_TIME_LIMIT = None

    # ======================================================
    # APPLICATION
    # ======================================================

    FREE_TRIAL_DAYS = 7


class DevelopmentConfig(Config):

    DEBUG = True

    SESSION_COOKIE_SECURE = False


class ProductionConfig(Config):

    DEBUG = False

    SESSION_COOKIE_SECURE = True


class TestingConfig(Config):

    TESTING = True

    SESSION_COOKIE_SECURE = False


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}