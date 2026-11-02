from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.import_entity_link import ImportEntityLink
from backend.app.models.import_item import ImportItem
from backend.app.models.import_session import ImportSession
from backend.app.models.import_validation_issue import ImportValidationIssue


class ImportRepository:
    def create_session(
        self,
        db: Session,
        session_obj: ImportSession,
    ) -> ImportSession:
        db.add(session_obj)
        db.flush()
        return session_obj

    def get_session(
        self,
        db: Session,
        *,
        family_id: int,
        member_id: int,
        import_id: int,
    ) -> ImportSession | None:
        stmt = select(ImportSession).where(
            ImportSession.id == import_id,
            ImportSession.family_id == family_id,
            ImportSession.member_id == member_id,
        )
        return db.scalars(stmt).first()

    def list_sessions(
        self,
        db: Session,
        *,
        family_id: int,
        member_id: int,
    ) -> list[ImportSession]:
        stmt = (
            select(ImportSession)
            .where(
                ImportSession.family_id == family_id,
                ImportSession.member_id == member_id,
            )
            .order_by(ImportSession.created_at.desc(), ImportSession.id.desc())
        )
        return list(db.scalars(stmt).all())

    def find_by_hash(
        self,
        db: Session,
        *,
        family_id: int,
        member_id: int,
        source_hash: str,
    ) -> ImportSession | None:
        stmt = (
            select(ImportSession)
            .where(
                ImportSession.family_id == family_id,
                ImportSession.member_id == member_id,
                ImportSession.source_hash == source_hash,
            )
            .order_by(ImportSession.id.asc())
        )
        return db.scalars(stmt).first()

    def add_item(
        self,
        db: Session,
        item: ImportItem,
    ) -> ImportItem:
        db.add(item)
        db.flush()
        return item

    def clear_validation_issues(
        self,
        db: Session,
        import_session_id: int,
    ) -> None:
        stmt = select(ImportValidationIssue).where(
            ImportValidationIssue.import_session_id == import_session_id
        )
        for row in db.scalars(stmt).all():
            db.delete(row)
        db.flush()

    def add_validation_issue(
        self,
        db: Session,
        issue: ImportValidationIssue,
    ) -> ImportValidationIssue:
        db.add(issue)
        db.flush()
        return issue

    def add_entity_link(
        self,
        db: Session,
        link: ImportEntityLink,
    ) -> ImportEntityLink:
        db.add(link)
        db.flush()
        return link

