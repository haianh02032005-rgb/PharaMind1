from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.core.security import hash_password, normalize_email
from backend.app.models.user import User, UserStatus
from backend.app.modules.users.exceptions import UserAlreadyExistsError
from backend.app.modules.users.repository import UserRepository


class UserService:
    def __init__(self, repository: UserRepository | None = None) -> None:
        self.repository = repository or UserRepository()

    def get_by_id(self, db: Session, user_id: int) -> User | None:
        return self.repository.get_by_id(db, user_id)

    def get_by_email(self, db: Session, email: str) -> User | None:
        normalized_email = normalize_email(email)
        return self.repository.get_by_email(db, normalized_email)

    def create_user(
        self,
        db: Session,
        *,
        email: str,
        password: str,
        full_name: str,
    ) -> User:
        normalized_email = normalize_email(email)

        existing_user = self.repository.get_by_email(db, normalized_email)
        if existing_user is not None:
            raise UserAlreadyExistsError("Email already registered")

        user = User(
            email=normalized_email,
            password_hash=hash_password(password),
            full_name=full_name.strip(),
            status=UserStatus.ACTIVE.value,
            is_email_verified=False,
        )

        try:
            self.repository.create(db, user)
            db.commit()
            db.refresh(user)
        except IntegrityError as exc:
            db.rollback()
            raise UserAlreadyExistsError("Email already registered") from exc

        return user
