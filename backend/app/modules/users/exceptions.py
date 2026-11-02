from backend.app.core.exceptions import AppException, PermissionDeniedError


class UserAlreadyExistsError(AppException):
    """Raised when registering with an email that already exists."""

    status_code = 409
    default_detail = "Email already registered"


class UserNotFoundError(AppException):
    """Raised when a requested user cannot be found."""

    status_code = 404
    default_detail = "User not found"


class UserInactiveError(PermissionDeniedError):
    """Raised when a user's status is not ACTIVE."""

    status_code = 403
    default_detail = "User account is not active"


class UserBlockedError(UserInactiveError):
    """Raised when a user's status is BLOCKED."""

    status_code = 403
    default_detail = "User account is blocked"
