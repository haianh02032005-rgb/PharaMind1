from sqlalchemy.orm import Session

from backend.app.core.exceptions import (
    AuthenticationError,
    InvalidTokenError,
    TokenExpiredError,
)
from backend.app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    normalize_email,
    verify_password,
)
from backend.app.models.user import User, UserStatus
from backend.app.modules.auth.schema import (
    AccessTokenResponse,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
)
from backend.app.modules.users.exceptions import (
    UserBlockedError,
    UserInactiveError,
)
from backend.app.modules.users.repository import UserRepository
from backend.app.modules.users.service import UserService


class AuthService:
    def __init__(
        self,
        user_repository: UserRepository | None = None,
        user_service: UserService | None = None,
    ) -> None:
        self.user_repository = user_repository or UserRepository()
        self.user_service = user_service or UserService(self.user_repository)

    def register(self, db: Session, payload: RegisterRequest) -> User:
        return self.user_service.create_user(
            db,
            email=payload.email,
            password=payload.password,
            full_name=payload.full_name,
        )

    def login(self, db: Session, payload: LoginRequest) -> TokenResponse:
        email = normalize_email(payload.email)
        user = self.user_repository.get_by_email(db, email)

        if user is None or not verify_password(payload.password, user.password_hash):
            raise AuthenticationError("Invalid email or password")

        self._ensure_user_active(user)

        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        )

    def refresh_access_token(
        self,
        db: Session,
        refresh_token: str,
    ) -> AccessTokenResponse:
        try:
            payload = decode_token(refresh_token)
        except (TokenExpiredError, InvalidTokenError) as exc:
            raise AuthenticationError(str(exc)) from exc

        if payload.get("type") != "refresh":
            raise InvalidTokenError("Invalid token type")

        sub = payload.get("sub")
        if sub is None:
            raise InvalidTokenError("Invalid token subject")

        try:
            user_id = int(sub)
        except (TypeError, ValueError) as exc:
            raise InvalidTokenError("Invalid token subject") from exc

        user = self.user_repository.get_by_id(db, user_id)
        if user is None:
            raise AuthenticationError("User not found")

        self._ensure_user_active(user)

        new_access_token = create_access_token(user.id)
        return AccessTokenResponse(
            access_token=new_access_token,
            token_type="bearer",
        )

    @staticmethod
    def _ensure_user_active(user: User) -> None:
        if user.status == UserStatus.BLOCKED.value:
            raise UserBlockedError("User account is blocked")
        if user.status != UserStatus.ACTIVE.value:
            raise UserInactiveError("User account is not active")
