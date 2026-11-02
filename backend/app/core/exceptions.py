import jwt


class AppException(Exception):
    """Base application exception with HTTP status code and detail message."""

    status_code: int = 400
    default_detail: str = "Application error"

    def __init__(self, detail: str | None = None, status_code: int | None = None) -> None:
        self.detail = detail or self.default_detail
        if status_code is not None:
            self.status_code = status_code
        super().__init__(self.detail)


class AuthenticationError(AppException):
    """Raised when credentials or tokens are invalid."""

    status_code = 401
    default_detail = "Invalid authentication credentials"


class TokenExpiredError(AuthenticationError, jwt.ExpiredSignatureError):
    """Raised when a JWT token has expired."""

    status_code = 401
    default_detail = "Token has expired"


class InvalidTokenError(AuthenticationError, jwt.InvalidTokenError):
    """Raised when a JWT token is malformed or has an invalid signature/type."""

    status_code = 401
    default_detail = "Invalid token"


class PermissionDeniedError(AppException):
    """Raised when a user is not allowed to perform an action."""

    status_code = 403
    default_detail = "Operation not permitted"
