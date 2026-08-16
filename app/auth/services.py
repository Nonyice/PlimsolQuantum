"""
Authentication Service
PlimsolQuantum
"""

from datetime import datetime, timedelta
import secrets
import traceback

from flask import (
    request,
    flash,
    redirect,
    url_for,
    current_app,
)

from flask_login import (
    login_user,
    logout_user,
)

from app.models.user import User
from app.models.email_token import EmailToken

from app.repositories.user_repository import (
    UserRepository,
)

from app.repositories.role_repository import (
    RoleRepository,
)

from app.services.database_service import (
    DatabaseService,
)

from app.services.email_service import (
    EmailService,
)


class AuthService:

    user_repo = UserRepository()
    role_repo = RoleRepository()

    # ==========================================================
    # VERIFICATION URL
    # ==========================================================

    @staticmethod
    def _build_verification_url(token):

        base_url = current_app.config.get(
            "APP_BASE_URL"
        )

        if not base_url:

            return url_for(
                "auth.verify_email",
                token=token,
                _external=True,
            )

        base_url = base_url.rstrip("/")

        verification_path = url_for(
            "auth.verify_email",
            token=token,
        )

        return f"{base_url}{verification_path}"

    # ==========================================================
    # REGISTER
    # ==========================================================

    @classmethod
    def register(cls):

        try:

            print(
                "\n========== REGISTRATION STARTED =========="
            )

            first_name = request.form.get(
                "first_name",
                "",
            ).strip()

            last_name = request.form.get(
                "last_name",
                "",
            ).strip()

            username = request.form.get(
                "username",
                "",
            ).strip()

            email = request.form.get(
                "email",
                "",
            ).strip().lower()

            password = request.form.get(
                "password",
                "",
            )

            confirm_password = request.form.get(
                "confirm_password",
                "",
            )

            print(f"First name: {first_name}")
            print(f"Last name: {last_name}")
            print(f"Username: {username}")
            print(f"Email: {email}")
            print(
                f"Password received: {bool(password)}"
            )

            # --------------------------------------------------
            # VALIDATION
            # --------------------------------------------------

            if not first_name:

                flash(
                    "Registration failed: First name is required.",
                    "danger",
                )

                return redirect(
                    url_for("auth.register")
                )

            if not last_name:

                flash(
                    "Registration failed: Last name is required.",
                    "danger",
                )

                return redirect(
                    url_for("auth.register")
                )

            if not username:

                flash(
                    "Registration failed: Username is required.",
                    "danger",
                )

                return redirect(
                    url_for("auth.register")
                )

            if not email:

                flash(
                    "Registration failed: Email is required.",
                    "danger",
                )

                return redirect(
                    url_for("auth.register")
                )

            if not password:

                flash(
                    "Registration failed: Password is required.",
                    "danger",
                )

                return redirect(
                    url_for("auth.register")
                )

            if len(password) < 8:

                flash(
                    "Registration failed: Password must be at least 8 characters.",
                    "danger",
                )

                return redirect(
                    url_for("auth.register")
                )

            if password != confirm_password:

                flash(
                    "Registration failed: Passwords do not match.",
                    "danger",
                )

                return redirect(
                    url_for("auth.register")
                )

            # --------------------------------------------------
            # CHECK EMAIL
            # --------------------------------------------------

            print(
                "Checking existing email..."
            )

            existing_email = (
                cls.user_repo.get_by_email(email)
            )

            print(
                f"Existing email: {existing_email}"
            )

            if existing_email:

                print(
                    "STOP: Email already exists"
                )

                flash(
                    "Registration failed: This email is already registered.",
                    "warning",
                )

                return redirect(
                    url_for("auth.register")
                )

            # --------------------------------------------------
            # CHECK USERNAME
            # --------------------------------------------------

            print(
                "Checking existing username..."
            )

            existing_username = (
                cls.user_repo.get_by_username(
                    username
                )
            )

            print(
                f"Existing username: {existing_username}"
            )

            if existing_username:

                print(
                    "STOP: Username already exists"
                )

                flash(
                    "Registration failed: This username is already in use.",
                    "warning",
                )

                return redirect(
                    url_for("auth.register")
                )

            # --------------------------------------------------
            # FIND DEFAULT ROLE
            # --------------------------------------------------

            print(
                "Looking for default User role..."
            )

            role = cls.role_repo.get_by_name(
                "User"
            )

            print(
                f"Role found: {role}"
            )

            if role is None:

                print(
                    "STOP: Default User role does not exist."
                )

                flash(
                    "Registration failed: Default user role is unavailable.",
                    "danger",
                )

                return redirect(
                    url_for("auth.register")
                )

            # --------------------------------------------------
            # CREATE USER
            # --------------------------------------------------

            print(
                "Creating user object..."
            )

            user = User(
                first_name=first_name,
                last_name=last_name,
                username=username,
                email=email,
                role=role,
                email_verified=False,
                onboarding_completed=False,
                pqi_enabled=False,
            )

            # --------------------------------------------------
            # HASH PASSWORD
            # --------------------------------------------------

            print(
                "Hashing password..."
            )

            user.set_password(password)

            # --------------------------------------------------
            # SAVE USER
            # --------------------------------------------------

            print(
                "Adding user to database..."
            )

            DatabaseService.add(user)
            DatabaseService.commit()

            print(
                f"USER CREATED SUCCESSFULLY: {user}"
            )

            # --------------------------------------------------
            # CREATE EMAIL VERIFICATION TOKEN
            # --------------------------------------------------

            print(
                "Creating verification token..."
            )

            verification_token = (
                secrets.token_urlsafe(48)
            )

            email_token = EmailToken(
                user_id=user.id,
                token=verification_token,
                purpose="email_verification",
                expires_at=(
                    datetime.utcnow()
                    + timedelta(hours=1)
                ),
                used=False,
            )

            DatabaseService.add(email_token)
            DatabaseService.commit()

            print(
                "Verification token created successfully."
            )

            # --------------------------------------------------
            # BUILD VERIFICATION URL
            # --------------------------------------------------

            verification_url = (
                cls._build_verification_url(
                    verification_token
                )
            )

            print(
                f"Verification URL: {verification_url}"
            )

            # --------------------------------------------------
            # SEND VERIFICATION EMAIL
            # --------------------------------------------------

            email_body = f"""
Hello {user.first_name},

Welcome to Plimsol Quantum Intelligence.

Your account has been created successfully.

Please verify your email address by clicking the link below:

{verification_url}

This verification link will expire in 1 hour.

If you did not create this account, please ignore this email.

Regards,

PQI
"""

            print(
                f"Sending verification email to {user.email}..."
            )

            EmailService.send_email(
                subject=(
                    "Verify Your Plimsol Quantum Intelligence Account"
                ),
                recipients=[user.email],
                body=email_body,
            )

            print(
                f"Verification email sent successfully to {user.email}."
            )

            # --------------------------------------------------
            # SUCCESS
            # --------------------------------------------------

            flash(
                f"Registration successful! "
                f"A verification email has been sent to "
                f"{user.email}. "
                f"Please check your email and click the "
                f"verification link to verify your account "
                f"before logging in.",
                "success",
            )

            print(
                f"REGISTRATION SUCCESSFUL - "
                f"VERIFICATION EMAIL SENT TO: "
                f"{user.email}"
            )

            print(
                "========== REGISTRATION SUCCESS ==========\n"
            )

            return redirect(
                url_for("auth.login")
            )

        except Exception as exc:

            print(
                "\n========== REGISTRATION ERROR =========="
            )

            print(
                f"ERROR TYPE: {type(exc).__name__}"
            )

            print(
                f"ERROR MESSAGE: {exc}"
            )

            traceback.print_exc()

            try:
                DatabaseService.rollback()
            except Exception:
                pass

            flash(
                "Registration failed because of a system error: "
                f"{type(exc).__name__}.",
                "danger",
            )

            print(
                "========== REGISTRATION FAILED ==========\n"
            )

            return redirect(
                url_for("auth.register")
            )

    # ==========================================================
    # LOGIN
    # ==========================================================

    @classmethod
    def login(cls):

        try:

            print(
                "\n========== LOGIN STARTED =========="
            )

            email = request.form.get(
                "email",
                "",
            ).strip().lower()

            password = request.form.get(
                "password",
                "",
            )

            if not email:

                flash(
                    "Login failed: Email is required.",
                    "danger",
                )

                return redirect(
                    url_for("auth.login")
                )

            if not password:

                flash(
                    "Login failed: Password is required.",
                    "danger",
                )

                return redirect(
                    url_for("auth.login")
                )

            print(
                f"Looking up user: {email}"
            )

            user = cls.user_repo.get_by_email(
                email
            )

            if not user:

                print(
                    "LOGIN FAILED: User does not exist."
                )

                flash(
                    "Login failed: Invalid email or password.",
                    "danger",
                )

                return redirect(
                    url_for("auth.login")
                )

            print(
                f"User found: {user}"
            )

            # --------------------------------------------------
            # PASSWORD
            # --------------------------------------------------

            if not user.check_password(
                password
            ):

                print(
                    "LOGIN FAILED: Incorrect password."
                )

                try:

                    user.record_failed_login()

                    DatabaseService.commit()

                except Exception:

                    DatabaseService.rollback()

                flash(
                    "Login failed: Invalid email or password.",
                    "danger",
                )

                return redirect(
                    url_for("auth.login")
                )

            # --------------------------------------------------
            # EMAIL VERIFICATION
            # --------------------------------------------------

            if not user.email_verified:

                print(
                    "LOGIN BLOCKED: Email not verified."
                )

                flash(
                    f"Login blocked: Your email address "
                    f"{user.email} has not been verified. "
                    f"Please check your email and click the "
                    f"verification link before logging in.",
                    "warning",
                )

                return redirect(
                    url_for("auth.login")
                )

            # --------------------------------------------------
            # SUCCESSFUL LOGIN
            # --------------------------------------------------

            user.record_successful_login()

            DatabaseService.commit()

            login_user(
                user,
                remember=True,
            )

            print(
                f"LOGIN SUCCESSFUL: {user.username}"
            )

            # --------------------------------------------------
            # FORCE ONBOARDING FOR INCOMPLETE USERS
            # --------------------------------------------------

            print(
                "------------------------------------------"
            )

            print(
                "CHECKING ONBOARDING STATUS"
            )

            print(
                f"User: {user.username}"
            )

            print(
                f"onboarding_completed value: "
                f"{user.onboarding_completed}"
            )

            print(
                f"onboarding_completed type: "
                f"{type(user.onboarding_completed).__name__}"
            )

            print(
                "------------------------------------------"
            )

            if user.onboarding_completed is not True:

                print(
                    "ONBOARDING NOT COMPLETED"
                )

                print(
                    "REDIRECTING USER TO:"
                )

                print(
                    "/onboarding/"
                )

                flash(
                    "Welcome to Plimsol Quantum! "
                    "Please complete your onboarding.",
                    "success",
                )

                print(
                    "========== LOGIN → ONBOARDING ==========\n"
                )

                return redirect(
                    url_for(
                        "onboarding.welcome"
                    )
                )

            # --------------------------------------------------
            # COMPLETED USER → DASHBOARD
            # --------------------------------------------------

            print(
                "ONBOARDING ALREADY COMPLETED"
            )

            print(
                "REDIRECTING USER TO DASHBOARD"
            )

            flash(
                f"Welcome back, {user.first_name}!",
                "success",
            )

            print(
                "========== LOGIN → DASHBOARD ==========\n"
            )

            return redirect(
                url_for(
                    "dashboard.index"
                )
            )

        except Exception as exc:

            print(
                "\n========== LOGIN ERROR =========="
            )

            print(
                f"ERROR TYPE: {type(exc).__name__}"
            )

            print(
                f"ERROR MESSAGE: {exc}"
            )

            traceback.print_exc()

            try:
                DatabaseService.rollback()
            except Exception:
                pass

            flash(
                "Login failed because of a system error: "
                f"{type(exc).__name__}.",
                "danger",
            )

            return redirect(
                url_for("auth.login")
            )

    # ==========================================================
    # VERIFY EMAIL
    # ==========================================================

    @classmethod
    def verify_email(cls, token):

        try:

            print(
                "\n========== EMAIL VERIFICATION STARTED =========="
            )

            if not token:

                flash(
                    "Email verification failed: "
                    "Invalid verification link.",
                    "danger",
                )

                return redirect(
                    url_for("auth.login")
                )

            email_token = (
                EmailToken.query.filter_by(
                    token=token,
                    purpose="email_verification",
                ).first()
            )

            if not email_token:

                print(
                    "Verification token does not exist."
                )

                flash(
                    "Email verification failed: "
                    "Invalid verification link.",
                    "danger",
                )

                return redirect(
                    url_for("auth.login")
                )

            if not email_token.is_valid:

                print(
                    "Verification token is expired "
                    "or already used."
                )

                flash(
                    "Email verification failed: "
                    "This verification link has expired "
                    "or has already been used. "
                    "Please request a new verification email.",
                    "warning",
                )

                return redirect(
                    url_for("auth.login")
                )

            user = email_token.user

            if not user:

                flash(
                    "Email verification failed: "
                    "User account not found.",
                    "danger",
                )

                return redirect(
                    url_for("auth.login")
                )

            # --------------------------------------------------
            # ALREADY VERIFIED
            # --------------------------------------------------

            if user.email_verified:

                email_token.mark_used()

                DatabaseService.commit()

                flash(
                    "Your email is already verified. "
                    "You may log in.",
                    "info",
                )

                return redirect(
                    url_for("auth.login")
                )

            # --------------------------------------------------
            # VERIFY USER
            # --------------------------------------------------

            user.email_verified = True

            user.email_verified_at = (
                datetime.utcnow()
            )

            email_token.mark_used()

            DatabaseService.commit()

            print(
                f"EMAIL VERIFIED SUCCESSFULLY: {user.email}"
            )

            flash(
                f"Email verification successful! "
                f"{user.email} has now been verified. "
                f"You may log in.",
                "success",
            )

            print(
                "========== EMAIL VERIFICATION SUCCESS ==========\n"
            )

            return redirect(
                url_for("auth.login")
            )

        except Exception as exc:

            print(
                "\n========== EMAIL VERIFICATION ERROR =========="
            )

            print(
                f"ERROR TYPE: {type(exc).__name__}"
            )

            print(
                f"ERROR MESSAGE: {exc}"
            )

            traceback.print_exc()

            try:
                DatabaseService.rollback()
            except Exception:
                pass

            flash(
                "Email verification failed because of a "
                "system error: "
                f"{type(exc).__name__}.",
                "danger",
            )

            return redirect(
                url_for("auth.login")
            )

    # ==========================================================
    # RESEND VERIFICATION
    # ==========================================================

    @classmethod
    def resend_verification(cls):

        try:

            print(
                "\n========== RESEND VERIFICATION STARTED =========="
            )

            email = request.form.get(
                "email",
                "",
            ).strip().lower()

            if not email:

                flash(
                    "Verification email failed: "
                    "Email is required.",
                    "danger",
                )

                return redirect(
                    url_for(
                        "auth.resend_verification"
                    )
                )

            user = cls.user_repo.get_by_email(
                email
            )

            if not user:

                flash(
                    "Verification email could not be sent.",
                    "warning",
                )

                return redirect(
                    url_for(
                        "auth.resend_verification"
                    )
                )

            if user.email_verified:

                flash(
                    "This email address is already verified. "
                    "You can log in.",
                    "info",
                )

                return redirect(
                    url_for("auth.login")
                )

            # --------------------------------------------------
            # INVALIDATE OLD TOKENS
            # --------------------------------------------------

            old_tokens = (
                EmailToken.query.filter_by(
                    user_id=user.id,
                    purpose="email_verification",
                    used=False,
                ).all()
            )

            for old_token in old_tokens:

                old_token.mark_used()

            # --------------------------------------------------
            # CREATE NEW TOKEN
            # --------------------------------------------------

            new_token = secrets.token_urlsafe(48)

            email_token = EmailToken(
                user_id=user.id,
                token=new_token,
                purpose="email_verification",
                expires_at=(
                    datetime.utcnow()
                    + timedelta(hours=1)
                ),
                used=False,
            )

            DatabaseService.add(
                email_token
            )

            DatabaseService.commit()

            # --------------------------------------------------
            # BUILD NEW VERIFICATION URL
            # --------------------------------------------------

            verification_url = (
                cls._build_verification_url(
                    new_token
                )
            )

            print(
                f"New verification URL: "
                f"{verification_url}"
            )

            # --------------------------------------------------
            # SEND EMAIL
            # --------------------------------------------------

            email_body = f"""
Hello {user.first_name},

Here is your new Plimsol Quantum Intelligence
email verification link:

{verification_url}

This link expires in 1 hour.

Regards,

Plimsol Quantum Intelligence
"""

            print(
                f"Sending new verification email to "
                f"{user.email}..."
            )

            EmailService.send_email(
                subject=(
                    "New PQI Email Verification Link"
                ),
                recipients=[user.email],
                body=email_body,
            )

            print(
                f"New verification email sent successfully "
                f"to {user.email}."
            )

            # --------------------------------------------------
            # SUCCESS
            # --------------------------------------------------

            flash(
                f"A new verification email has been sent to "
                f"{user.email}. "
                f"Please check your inbox and click the "
                f"verification link to verify your account.",
                "success",
            )

            print(
                "========== RESEND VERIFICATION SUCCESS ==========\n"
            )

            return redirect(
                url_for("auth.login")
            )

        except Exception as exc:

            print(
                "\n========== RESEND VERIFICATION ERROR =========="
            )

            print(
                f"ERROR TYPE: {type(exc).__name__}"
            )

            print(
                f"ERROR MESSAGE: {exc}"
            )

            traceback.print_exc()

            try:
                DatabaseService.rollback()
            except Exception:
                pass

            flash(
                "Unable to resend verification email: "
                f"{type(exc).__name__}.",
                "danger",
            )

            return redirect(
                url_for(
                    "auth.resend_verification"
                )
            )

    # ==========================================================
    # FORGOT PASSWORD
    # ==========================================================

    @classmethod
    def forgot_password(cls):

        try:

            # Keep your existing forgot-password
            # implementation here.

            flash(
                "Password reset request received.",
                "info",
            )

            return redirect(
                url_for("auth.login")
            )

        except Exception as exc:

            print(
                f"Forgot password error: "
                f"{type(exc).__name__}: {exc}"
            )

            traceback.print_exc()

            try:
                DatabaseService.rollback()
            except Exception:
                pass

            flash(
                "Unable to process password reset request.",
                "danger",
            )

            return redirect(
                url_for("auth.forgot_password")
            )

    # ==========================================================
    # RESET PASSWORD
    # ==========================================================

    @classmethod
    def reset_password(cls, token):

        try:

            # Keep your existing reset-password
            # implementation here.

            flash(
                "Password reset completed.",
                "success",
            )

            return redirect(
                url_for("auth.login")
            )

        except Exception as exc:

            print(
                f"Reset password error: "
                f"{type(exc).__name__}: {exc}"
            )

            traceback.print_exc()

            try:
                DatabaseService.rollback()
            except Exception:
                pass

            flash(
                "Unable to reset password.",
                "danger",
            )

            return redirect(
                url_for("auth.login")
            )

    # ==========================================================
    # LOGOUT
    # ==========================================================

    @classmethod
    def logout(cls):

        try:

            logout_user()

            flash(
                "You have been logged out successfully.",
                "success",
            )

            return redirect(
                url_for("auth.login")
            )

        except Exception as exc:

            print(
                f"Logout error: "
                f"{type(exc).__name__}: {exc}"
            )

            flash(
                "Logout failed.",
                "danger",
            )

            return redirect(
                url_for("auth.login")
            )
