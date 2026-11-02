from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.core.security import normalize_email
from backend.app.models.family import Family
from backend.app.models.family_membership import FamilyMembership
from backend.app.models.user import User
from backend.app.modules.families.exceptions import (
    DuplicateFamilyMembershipError,
    FamilyArchivedError,
    InsufficientFamilyPermissionError,
    MembershipNotFoundError,
    OwnerModificationNotAllowedError,
)
from backend.app.modules.families.repository import FamilyRepository
from backend.app.modules.families.schema import (
    FamilyCreateRequest,
    FamilyListItem,
    FamilyListResponse,
    FamilyMembershipCreateRequest,
    FamilyMembershipListResponse,
    FamilyMembershipResponse,
    FamilyMembershipUpdateRequest,
    FamilyMemberUserSummary,
    FamilyResponse,
    FamilyUpdateRequest,
)
from backend.app.modules.users.exceptions import UserNotFoundError
from backend.app.modules.users.repository import UserRepository
from backend.app.shared.enums import FamilyRole, FamilyStatus


class FamilyService:
    def __init__(
        self,
        repository: FamilyRepository | None = None,
        user_repository: UserRepository | None = None,
    ) -> None:
        self.repository = repository or FamilyRepository()
        self.user_repository = user_repository or UserRepository()

    def create_family(
        self,
        db: Session,
        user: User,
        payload: FamilyCreateRequest,
    ) -> FamilyResponse:
        family = Family(
            name=payload.name.strip(),
            description=payload.description,
            status=FamilyStatus.ACTIVE.value,
        )

        try:
            created_family = self.repository.create_family(db, family)
            membership = FamilyMembership(
                family_id=created_family.id,
                user_id=user.id,
                role=FamilyRole.OWNER.value,
            )
            created_membership = self.repository.create_membership(db, membership)
            db.commit()
            db.refresh(created_family)
            db.refresh(created_membership)
        except Exception:
            db.rollback()
            raise

        return self._to_family_response(created_family, created_membership.role)

    def list_my_families(
        self,
        db: Session,
        user: User,
        *,
        include_archived: bool = False,
    ) -> FamilyListResponse:
        pairs = self.repository.list_families_for_user(
            db,
            user.id,
            include_archived=include_archived,
        )
        items = [
            FamilyListItem(
                id=family.id,
                name=family.name,
                description=family.description,
                status=family.status,
                my_role=membership.role,
                created_at=family.created_at,
            )
            for family, membership in pairs
        ]
        return FamilyListResponse(items=items)

    def get_family_detail(
        self,
        membership: FamilyMembership,
    ) -> FamilyResponse:
        return self._to_family_response(membership.family, membership.role)

    def update_family(
        self,
        db: Session,
        membership: FamilyMembership,
        payload: FamilyUpdateRequest,
    ) -> FamilyResponse:
        self._ensure_roles(membership, FamilyRole.OWNER, FamilyRole.ADMIN)
        self._ensure_family_active(membership.family)

        fields_set = payload.model_fields_set
        name = payload.name.strip() if "name" in fields_set and payload.name is not None else None
        update_description = "description" in fields_set

        updated = self.repository.update_family(
            db,
            membership.family,
            name=name,
            description=payload.description,
            update_description=update_description,
        )
        db.commit()
        db.refresh(updated)
        return self._to_family_response(updated, membership.role)

    def archive_family(
        self,
        db: Session,
        membership: FamilyMembership,
    ) -> FamilyResponse:
        self._ensure_roles(membership, FamilyRole.OWNER)

        updated = self.repository.update_family(
            db,
            membership.family,
            status=FamilyStatus.ARCHIVED.value,
        )
        db.commit()
        db.refresh(updated)
        return self._to_family_response(updated, membership.role)

    def restore_family(
        self,
        db: Session,
        membership: FamilyMembership,
    ) -> FamilyResponse:
        self._ensure_roles(membership, FamilyRole.OWNER)

        updated = self.repository.update_family(
            db,
            membership.family,
            status=FamilyStatus.ACTIVE.value,
        )
        db.commit()
        db.refresh(updated)
        return self._to_family_response(updated, membership.role)

    def list_memberships(
        self,
        db: Session,
        membership: FamilyMembership,
    ) -> FamilyMembershipListResponse:
        rows = self.repository.list_memberships(db, membership.family_id)
        items = [self._to_membership_response(row) for row in rows]
        return FamilyMembershipListResponse(items=items)

    def add_membership(
        self,
        db: Session,
        actor_membership: FamilyMembership,
        payload: FamilyMembershipCreateRequest,
    ) -> FamilyMembershipResponse:
        self._ensure_roles(actor_membership, FamilyRole.OWNER, FamilyRole.ADMIN)
        self._ensure_family_active(actor_membership.family)

        if payload.role == FamilyRole.OWNER:
            raise OwnerModificationNotAllowedError("Cannot assign OWNER role")

        normalized_email = normalize_email(payload.email)
        target_user = self.user_repository.get_by_email(db, normalized_email)
        if target_user is None:
            raise UserNotFoundError("User account not found")

        existing = self.repository.get_membership(
            db,
            family_id=actor_membership.family_id,
            user_id=target_user.id,
        )
        if existing is not None:
            raise DuplicateFamilyMembershipError("User already belongs to this family")

        new_membership = FamilyMembership(
            family_id=actor_membership.family_id,
            user_id=target_user.id,
            role=payload.role.value,
        )

        try:
            created = self.repository.create_membership(db, new_membership)
            db.commit()
            db.refresh(created)
        except IntegrityError as exc:
            db.rollback()
            raise DuplicateFamilyMembershipError(
                "User already belongs to this family"
            ) from exc

        return self._to_membership_response(created)

    def update_membership_role(
        self,
        db: Session,
        actor_membership: FamilyMembership,
        membership_id: int,
        payload: FamilyMembershipUpdateRequest,
    ) -> FamilyMembershipResponse:
        self._ensure_roles(actor_membership, FamilyRole.OWNER)
        self._ensure_family_active(actor_membership.family)

        if payload.role == FamilyRole.OWNER:
            raise OwnerModificationNotAllowedError("Cannot assign OWNER role")

        target = self.repository.get_membership_by_id(
            db,
            family_id=actor_membership.family_id,
            membership_id=membership_id,
        )
        if target is None:
            raise MembershipNotFoundError("Membership not found")

        if target.role == FamilyRole.OWNER.value:
            raise OwnerModificationNotAllowedError("Cannot modify owner membership")

        updated = self.repository.update_membership_role(
            db,
            target,
            payload.role.value,
        )
        db.commit()
        db.refresh(updated)
        return self._to_membership_response(updated)

    def remove_membership(
        self,
        db: Session,
        actor_membership: FamilyMembership,
        membership_id: int,
    ) -> None:
        self._ensure_roles(actor_membership, FamilyRole.OWNER, FamilyRole.ADMIN)
        self._ensure_family_active(actor_membership.family)

        target = self.repository.get_membership_by_id(
            db,
            family_id=actor_membership.family_id,
            membership_id=membership_id,
        )
        if target is None:
            raise MembershipNotFoundError("Membership not found")

        if target.role == FamilyRole.OWNER.value:
            raise OwnerModificationNotAllowedError("Cannot modify owner membership")

        if (
            actor_membership.role == FamilyRole.ADMIN.value
            and target.role == FamilyRole.ADMIN.value
        ):
            raise InsufficientFamilyPermissionError(
                "Insufficient family permission"
            )

        self.repository.delete_membership(db, target)
        db.commit()

    @staticmethod
    def _ensure_roles(
        membership: FamilyMembership,
        *allowed_roles: FamilyRole,
    ) -> None:
        allowed_values = {role.value for role in allowed_roles}
        if membership.role not in allowed_values:
            raise InsufficientFamilyPermissionError("Insufficient family permission")

    @staticmethod
    def _ensure_family_active(family: Family) -> None:
        if family.status != FamilyStatus.ACTIVE.value:
            raise FamilyArchivedError("Family archived")

    @staticmethod
    def _to_family_response(family: Family, my_role: str) -> FamilyResponse:
        return FamilyResponse(
            id=family.id,
            name=family.name,
            description=family.description,
            status=family.status,
            my_role=my_role,
            created_at=family.created_at,
            updated_at=family.updated_at,
        )

    @staticmethod
    def _to_membership_response(
        membership: FamilyMembership,
    ) -> FamilyMembershipResponse:
        return FamilyMembershipResponse(
            id=membership.id,
            family_id=membership.family_id,
            user=FamilyMemberUserSummary.model_validate(membership.user),
            role=membership.role,
            created_at=membership.created_at,
        )
