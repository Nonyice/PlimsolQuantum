import secrets

from app.extensions import db
from app.models.email_token import EmailToken
from app.models.role import Role
from app.models.user import User

from app.services.activity_log_service import ActivityLogService
from app.services.email_service import EmailService
from app.services.subscription_service import SubscriptionService


class AuthenticationService:

    @staticmethod
    def register_user(form):

        role = Role.query.filter_by(
            name="User"
        ).first()

        user = User(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            username=form.username.data,
            email=form.email.data.lower(),
            role=role,
        )

        user.set_password(
            form.password.data
        )

        db.session.add(user)

        db.session.flush()

        SubscriptionService.create_trial(user)

        token = EmailToken(
            user_id=user.id,
            token=secrets.token_urlsafe(32),
            purpose="VERIFY_EMAIL",
        )

        db.session.add(token)

        EmailService.send_email(
            subject="Verify your PlimsolQuantum account",
            recipients=[user.email],
            body=f"Verification token:\n\n{token.token}",
        )

        db.session.commit()

        ActivityLogService.log(
            user,
            "REGISTER",
            "User account created.",
        )

        return user