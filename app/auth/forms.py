"""
Authentication forms for PlimsolQuantum.
"""

from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    SubmitField,
    EmailField,
)
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    Length,
    ValidationError,
)

from app.models.user import User


class RegistrationForm(FlaskForm):

    first_name = StringField(
        "First Name",
        validators=[
            DataRequired(),
            Length(min=2, max=100),
        ],
    )

    last_name = StringField(
        "Last Name",
        validators=[
            DataRequired(),
            Length(min=2, max=100),
        ],
    )

    username = StringField(
        "Username",
        validators=[
            DataRequired(),
            Length(min=4, max=50),
        ],
    )

    email = EmailField(
        "Email",
        validators=[
            DataRequired(),
            Email(),
        ],
    )

    password = PasswordField(
        "Password",
        validators=[
            DataRequired(),
            Length(min=8),
        ],
    )

    confirm_password = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(),
            EqualTo(
                "password",
                message="Passwords must match.",
            ),
        ],
    )

    submit = SubmitField("Create Account")

    def validate_email(self, field):

        if User.query.filter_by(
            email=field.data.lower()
        ).first():

            raise ValidationError(
                "Email already registered."
            )

    def validate_username(self, field):

        if User.query.filter_by(
            username=field.data
        ).first():

            raise ValidationError(
                "Username already exists."
            )


class LoginForm(FlaskForm):

    email = EmailField(
        "Email",
        validators=[
            DataRequired(),
            Email(),
        ],
    )

    password = PasswordField(
        "Password",
        validators=[
            DataRequired(),
        ],
    )

    submit = SubmitField("Login")


class ForgotPasswordForm(FlaskForm):

    email = EmailField(
        "Email",
        validators=[
            DataRequired(),
            Email(),
        ],
    )

    submit = SubmitField(
        "Send Reset Link"
    )


class ResetPasswordForm(FlaskForm):

    password = PasswordField(
        "New Password",
        validators=[
            DataRequired(),
            Length(min=8),
        ],
    )

    confirm_password = PasswordField(
        "Confirm Password",
        validators=[
            EqualTo("password"),
            DataRequired(),
        ],
    )

    submit = SubmitField(
        "Reset Password"
    )


class TradingPinForm(FlaskForm):

    pin = PasswordField(
        "Trading PIN",
        validators=[
            DataRequired(),
            Length(min=4, max=6),
        ],
    )

    confirm_pin = PasswordField(
        "Confirm PIN",
        validators=[
            EqualTo(
                "pin",
                message="PINs do not match.",
            ),
            DataRequired(),
        ],
    )

    submit = SubmitField(
        "Create Trading PIN"
    )


class TradingPinVerificationForm(FlaskForm):

    pin = PasswordField(
        "Trading PIN",
        validators=[
            DataRequired(),
            Length(min=4, max=6),
        ],
    )

    submit = SubmitField(
        "Verify PIN"
    )


class ResendVerificationForm(FlaskForm):

    email = EmailField(
        "Email",
        validators=[
            DataRequired(),
            Email(),
        ],
    )

    submit = SubmitField(
        "Resend Verification"
    )