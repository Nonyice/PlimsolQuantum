class AuthenticationError(Exception):
    """Raised when authentication fails."""


class UserAlreadyExists(AuthenticationError):
    """User already exists."""


class InvalidCredentials(AuthenticationError):
    """Invalid email or password."""


class EmailNotVerified(AuthenticationError):
    """Email address has not been verified."""


class InvalidToken(AuthenticationError):
    """Invalid verification token."""