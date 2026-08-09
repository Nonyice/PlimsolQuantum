"""
Authentication Service
PlimsolQuantum
"""

from __future__ import annotations

import secrets
from datetime import datetime

from flask import current_app
from flask_login import login_user, logout_user

from app.extensions import db

from app.models.user import User
from app.models.role import Role
from app.models.trial import Trial
from app.models.email_token import EmailToken

from app.services.email_service import EmailService
from app.services.activity_log_service import ActivityLogService


class AuthenticationService:
    """
    Handles all authentication business logic.
    """

    @staticmethod
    def register_user(form):
        """
        Registers a brand-new user.
        """

        role = Role.query.filter_by(
            name="User"
        ).first()

        if role is None:
            raise ValueError(
                "Default user role not found."
            )

        user = User(
            first_name=form.first_name.data.strip(),
            last_name=form.last_name.data.strip(),
            username=form.username.data.strip(),
            email=form.email.data.lower().strip(),
            role=role,
        )

        user.set_password(
            form.password.data
        )

        db.session.add(user)

        db.session.flush()

        AuthenticationService.create_trial(user)
        AuthenticationService.assign_starter_plan(user)

        token = AuthenticationService.create_email_token(
            user=user,
            purpose="VERIFY_EMAIL",
        )

        db.session.commit()

        EmailService.send_verification_email(
            user=user,
            token=token.token,
        )

        ActivityLogService.log(
            user=user,
            action="REGISTER",
            description="User successfully registered.",
        )

        return user

    @staticmethod
    def login(email, password):
        """
        Login a verified user.
        """

        user = User.query.filter_by(
            email=email.lower()
        ).first()

        if not user:
            return None, "Invalid email or password."

        if user.locked_until:

            if datetime.utcnow() < user.locked_until:

                return (
                    None,
                    "Account temporarily locked.",
                )

        if not user.check_password(password):

            user.record_failed_login()

            db.session.commit()

            return (
                None,
                "Invalid email or password.",
            )

        if not user.email_verified:

            return (
                None,
                "Verify your email first.",
            )

        user.record_successful_login()

        db.session.commit()

        login_user(
            user,
            remember=True,
        )

        ActivityLogService.log(
            user=user,
            action="LOGIN",
            description="Successful login.",
        )

        if not user.onboarding_completed:
            return user, "ONBOARDING"

    @staticmethod
    def logout():

        logout_user()

    @staticmethod
    def create_trial(user):

        trial = Trial(
            user_id=user.id
        )

        db.session.add(trial)

        return trial

    @staticmethod
    def create_email_token(
        user,
        purpose,
    ):

        token = EmailToken(
            user_id=user.id,
            token=secrets.token_urlsafe(48),
            purpose=purpose,
        )

        db.session.add(token)

        return token

    @staticmethod
    def verify_email(token_value):

        token = EmailToken.query.filter_by(
            token=token_value
        ).first()

        if token is None:

            return False, "Invalid token."

        if not token.is_valid:

            return False, "Token expired."

        user = token.user

        user.email_verified = True
        user.email_verified_at = datetime.utcnow()

        token.mark_used()

        db.session.commit()

        ActivityLogService.log(
            user=user,
            action="VERIFY_EMAIL",
            description="Email verified.",
        )

        return True, None
    
    @staticmethod
    def resend_verification(user):

        token = AuthenticationService.create_email_token(
            user=user,
            purpose="VERIFY_EMAIL",
        )

        db.session.commit()

        EmailService.send_verification_email(
            user=user,
            token=token.token,
        )

        ActivityLogService.log(
            user=user,
            action="RESEND_VERIFICATION",
            description="Verification email resent.",
        )


    @staticmethod
    def forgot_password(user):

        token = AuthenticationService.create_email_token(
            user=user,
            purpose="RESET_PASSWORD",
        )

        db.session.commit()

        EmailService.send_password_reset(
            user=user,
            token=token.token,
        )

        ActivityLogService.log(
            user=user,
            action="PASSWORD_RESET_REQUEST",
            description="Password reset requested.",
        )

    @staticmethod
    def reset_password(
        token_value,
        new_password,
    ):

        token = EmailToken.query.filter_by(
            token=token_value
        ).first()

        if token is None:

            return False, "Invalid token."

        if not token.is_valid:

            return False, "Expired token."

        user = token.user

        user.set_password(
            new_password
        )

        token.mark_used()

        db.session.commit()

        ActivityLogService.log(
            user=user,
            action="PASSWORD_RESET",
            description="Password successfully changed.",
        )

    @staticmethod
    def assign_starter_plan(user):

        from datetime import timedelta

        from app.models.subscription import Subscription
        from app.models.subscription_plan import SubscriptionPlan

        plan = SubscriptionPlan.query.filter_by(
            is_trial=True
        ).first()

        if not plan:
            return

        subscription = Subscription(
            user_id=user.id,
            plan_id=plan.id,
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=plan.duration_days),
        )

        db.session.add(subscription)

        return True, None