from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from backend.app.models.family import Family
from backend.app.models.family_membership import FamilyMembership
from backend.app.shared.enums import FamilyRole, FamilyStatus


class FamilyRepository:
    def create_family(self, db: Session, family: Family) -> Family:
        db.add(family)
        db.flush()
        db.refresh(family)
        return family

    def get_family_by_id(self, db: Session, family_id: int) -> Family | None:
        return db.get(Family, family_id)

    def list_families_for_user(
        self,
        db: Session,
        user_id: int,
        *,
        include_archived: bool = False,
    ) -> list[tuple[Family, FamilyMembership]]:
        stmt = (
            select(Family, FamilyMembership)
            .join(FamilyMembership, FamilyMembership.family_id == Family.id)
            .where(FamilyMembership.user_id == user_id)
        )

        if include_archived:
            stmt = stmt.where(
                or_(
                    Family.status == FamilyStatus.ACTIVE.value,
                    FamilyMembership.role == FamilyRole.OWNER.value,
                )
            )
        else:
            stmt = stmt.where(Family.status == FamilyStatus.ACTIVE.value)

        stmt = stmt.order_by(Family.id.asc())
        rows = db.execute(stmt).all()
        return [(row[0], row[1]) for row in rows]

    def update_family(
        self,
        db: Session,
        family: Family,
        *,
        name: str | None = None,
        description: str | None = None,
        update_description: bool = False,
        status: str | None = None,
    ) -> Family:
        if name is not None:
            family.name = name
        if update_description:
            family.description = description
        if status is not None:
            family.status = status

        db.add(family)
        db.flush()
        db.refresh(family)
        return family

    def get_membership(
        self,
        db: Session,
        family_id: int,
        user_id: int,
    ) -> FamilyMembership | None:
        stmt = (
            select(FamilyMembership)
            .options(
                joinedload(FamilyMembership.family),
                joinedload(FamilyMembership.user),
            )
            .where(
                FamilyMembership.family_id == family_id,
                FamilyMembership.user_id == user_id,
            )
        )
        return db.execute(stmt).scalar_one_or_none()

    def get_membership_by_id(
        self,
        db: Session,
        family_id: int,
        membership_id: int,
    ) -> FamilyMembership | None:
        stmt = (
            select(FamilyMembership)
            .options(
                joinedload(FamilyMembership.family),
                joinedload(FamilyMembership.user),
            )
            .where(
                FamilyMembership.id == membership_id,
                FamilyMembership.family_id == family_id,
            )
        )
        return db.execute(stmt).scalar_one_or_none()

    def list_memberships(
        self,
        db: Session,
        family_id: int,
    ) -> list[FamilyMembership]:
        stmt = (
            select(FamilyMembership)
            .options(joinedload(FamilyMembership.user))
            .where(FamilyMembership.family_id == family_id)
            .order_by(FamilyMembership.id.asc())
        )
        return list(db.execute(stmt).scalars().all())

    def create_membership(
        self,
        db: Session,
        membership: FamilyMembership,
    ) -> FamilyMembership:
        db.add(membership)
        db.flush()
        db.refresh(membership)
        return membership

    def update_membership_role(
        self,
        db: Session,
        membership: FamilyMembership,
        role: str,
    ) -> FamilyMembership:
        membership.role = role
        db.add(membership)
        db.flush()
        db.refresh(membership)
        return membership

    def delete_membership(
        self,
        db: Session,
        membership: FamilyMembership,
    ) -> None:
        db.delete(membership)
        db.flush()
