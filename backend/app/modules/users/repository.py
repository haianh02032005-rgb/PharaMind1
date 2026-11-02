from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.user import User


class UserRepository:
    def get_by_id(self, db: Session, user_id: int) -> User | None:
        return db.get(User, user_id)

    def find_by_id(self, db: Session, user_id: int) -> User | None:
        return self.get_by_id(db, user_id)

    def get_by_email(self, db: Session, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        return db.execute(stmt).scalar_one_or_none()

    def find_by_email(self, db: Session, email: str) -> User | None:
        return self.get_by_email(db, email)

    def create(self, db: Session, user: User) -> User:
        db.add(user)
        db.flush()
        db.refresh(user)
        return user
