from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from backend.app.models.family import Family
from backend.app.models.family_medication import FamilyMedication
from backend.app.models.family_member import FamilyMember
from backend.app.models.family_membership import FamilyMembership
from backend.app.models.medication_catalog import MedicationCatalog
from backend.app.models.member_medication import MemberMedication
from backend.app.modules.families.exceptions import (
    FamilyArchivedError,
    InsufficientFamilyPermissionError,
)
from backend.app.modules.medications.enums import (
    MedicationSource,
    MedicationStatus,
)
from backend.app.modules.medications.exceptions import (
    DuplicateMemberMedicationLinkError,
    MedicationArchivedError,
    MedicationNotFoundError,
    MemberMedicationLinkNotFoundError,
)
from backend.app.modules.medications.repository import MedicationRepository
from backend.app.modules.medications.schema import (
    InventoryUpdateRequest,
    MedicationCreateRequest,
    MedicationListResponse,
    MedicationMemberLinkRequest,
    MedicationMemberListResponse,
    MedicationMemberResponse,
    MedicationResponse,
    MedicationUpdateRequest,
)
from backend.app.modules.members.exceptions import (
    MemberArchivedError,
    MemberNotFoundError,
)
from backend.app.modules.members.repository import MemberRepository
from backend.app.shared.enums import FamilyRole, FamilyStatus, MemberStatus


WRITE_MEDICATION_ROLES = (
    FamilyRole.OWNER,
    FamilyRole.ADMIN,
    FamilyRole.CAREGIVER,
)

ADMIN_MEDICATION_ROLES = (
    FamilyRole.OWNER,
    FamilyRole.ADMIN,
)


class MedicationService:
    def __init__(
        self,
        repository: MedicationRepository | None = None,
        member_repository: MemberRepository | None = None,
    ) -> None:
        self.repository = repository or MedicationRepository()
        self.member_repository = member_repository or MemberRepository()

    # ------------------------------------------------------------------
    # Medication CRUD & Inventory Operations
    # ------------------------------------------------------------------

    def create_medication(
        self,
        db: Session,
        membership: FamilyMembership,
        payload: MedicationCreateRequest,
    ) -> MedicationResponse:
        self._ensure_roles(membership, *WRITE_MEDICATION_ROLES)
        self._ensure_family_active(membership.family)

        dosage_form_val = (
            payload.dosage_form.value
            if payload.dosage_form is not None
            else None
        )

        try:
            catalog = self.repository.find_catalog(
                db,
                name=payload.name,
                active_ingredient=payload.active_ingredient,
                strength=payload.strength,
                dosage_form=dosage_form_val,
                manufacturer=payload.manufacturer,
            )
            if catalog is None:
                catalog = self.repository.create_catalog(
                    db,
                    MedicationCatalog(
                        name=payload.name,
                        active_ingredient=payload.active_ingredient,
                        strength=payload.strength,
                        dosage_form=dosage_form_val,
                        manufacturer=payload.manufacturer,
                        description=payload.description,
                        source=MedicationSource.USER_ENTERED.value,
                    ),
                )

            initial_status = self._compute_active_status(
                quantity=payload.quantity,
                expiration_date=payload.expiration_date,
            )

            family_medication = FamilyMedication(
                family_id=membership.family_id,
                catalog_id=catalog.id,
                quantity=payload.quantity,
                unit=payload.unit.value,
                expiration_date=payload.expiration_date,
                opened_at=payload.opened_at,
                low_stock_threshold=payload.low_stock_threshold,
                status=initial_status,
                notes=payload.notes,
            )
            created = self.repository.create_family_medication(
                db, family_medication
            )
            db.commit()
            db.refresh(created)
        except Exception:
            db.rollback()
            raise

        return MedicationResponse.from_model(created)

    def list_medications(
        self,
        db: Session,
        membership: FamilyMembership,
        *,
        status: MedicationStatus | None = None,
        search: str | None = None,
        include_archived: bool = False,
    ) -> MedicationListResponse:
        rows = self.repository.list_family_medications(
            db,
            family_id=membership.family_id,
            status=status.value if status is not None else None,
            search=search,
            include_archived=include_archived,
        )
        return MedicationListResponse(
            items=[MedicationResponse.from_model(row) for row in rows]
        )

    def get_medication_detail(
        self,
        db: Session,
        membership: FamilyMembership,
        medication_id: int,
    ) -> MedicationResponse:
        medication = self._get_scoped_medication(db, membership, medication_id)
        return MedicationResponse.from_model(medication)

    def update_medication(
        self,
        db: Session,
        membership: FamilyMembership,
        medication_id: int,
        payload: MedicationUpdateRequest,
    ) -> MedicationResponse:
        self._ensure_roles(membership, *WRITE_MEDICATION_ROLES)
        self._ensure_family_active(membership.family)

        medication = self._get_scoped_medication(db, membership, medication_id)
        self._ensure_medication_not_archived(medication)

        changes: dict[str, Any] = {}
        for field_name in payload.model_fields_set:
            value = getattr(payload, field_name)
            if field_name == "unit" and value is not None:
                value = value.value
            changes[field_name] = value

        if changes:
            new_quantity = changes.get("quantity", medication.quantity)
            new_expiration = changes.get(
                "expiration_date", medication.expiration_date
            )
            changes["status"] = self._compute_active_status(
                quantity=new_quantity,
                expiration_date=new_expiration,
            )
            medication = self.repository.update_family_medication(
                db, medication, **changes
            )
            db.commit()
            db.refresh(medication)

        return MedicationResponse.from_model(medication)

    def update_inventory(
        self,
        db: Session,
        membership: FamilyMembership,
        medication_id: int,
        payload: InventoryUpdateRequest,
    ) -> MedicationResponse:
        self._ensure_roles(membership, *WRITE_MEDICATION_ROLES)
        self._ensure_family_active(membership.family)

        medication = self._get_scoped_medication(db, membership, medication_id)
        self._ensure_medication_not_archived(medication)

        changes: dict[str, Any] = {
            "quantity": payload.quantity,
            "status": self._compute_active_status(
                quantity=payload.quantity,
                expiration_date=medication.expiration_date,
            ),
        }
        if "low_stock_threshold" in payload.model_fields_set:
            changes["low_stock_threshold"] = payload.low_stock_threshold

        medication = self.repository.update_family_medication(
            db, medication, **changes
        )
        db.commit()
        db.refresh(medication)
        return MedicationResponse.from_model(medication)

    def archive_medication(
        self,
        db: Session,
        membership: FamilyMembership,
        medication_id: int,
    ) -> MedicationResponse:
        self._ensure_roles(membership, *ADMIN_MEDICATION_ROLES)
        self._ensure_family_active(membership.family)

        medication = self._get_scoped_medication(db, membership, medication_id)
        updated = self.repository.archive_medication(db, medication)
        db.commit()
        db.refresh(updated)
        return MedicationResponse.from_model(updated)

    def restore_medication(
        self,
        db: Session,
        membership: FamilyMembership,
        medication_id: int,
    ) -> MedicationResponse:
        self._ensure_roles(membership, *ADMIN_MEDICATION_ROLES)
        self._ensure_family_active(membership.family)

        medication = self._get_scoped_medication(db, membership, medication_id)
        restored_status = self._compute_active_status(
            quantity=medication.quantity,
            expiration_date=medication.expiration_date,
        )
        updated = self.repository.restore_medication(
            db, medication, restored_status
        )
        db.commit()
        db.refresh(updated)
        return MedicationResponse.from_model(updated)

    # ------------------------------------------------------------------
    # Member <-> Medication Link Operations
    # ------------------------------------------------------------------

    def link_member(
        self,
        db: Session,
        membership: FamilyMembership,
        medication_id: int,
        payload: MedicationMemberLinkRequest,
    ) -> MedicationMemberResponse:
        self._ensure_roles(membership, *WRITE_MEDICATION_ROLES)
        self._ensure_family_active(membership.family)

        medication = self._get_scoped_medication(db, membership, medication_id)
        self._ensure_medication_not_archived(medication)

        member = self._get_scoped_member(db, membership, payload.member_id)
        self._ensure_member_active(member)

        existing = self.repository.get_member_link(
            db,
            member_id=member.id,
            family_medication_id=medication.id,
        )
        if existing is not None:
            raise DuplicateMemberMedicationLinkError(
                "Medication is already linked to this member"
            )

        link = MemberMedication(
            member_id=member.id,
            family_medication_id=medication.id,
        )
        self.repository.create_member_link(db, link)
        db.commit()
        return MedicationMemberResponse.model_validate(member)

    def unlink_member(
        self,
        db: Session,
        membership: FamilyMembership,
        medication_id: int,
        member_id: int,
    ) -> None:
        self._ensure_roles(membership, *WRITE_MEDICATION_ROLES)
        self._ensure_family_active(membership.family)

        medication = self._get_scoped_medication(db, membership, medication_id)
        self._ensure_medication_not_archived(medication)

        member = self._get_scoped_member(db, membership, member_id)
        link = self.repository.get_member_link(
            db,
            member_id=member.id,
            family_medication_id=medication.id,
        )
        if link is None:
            raise MemberMedicationLinkNotFoundError(
                "Member medication link not found"
            )

        self.repository.delete_member_link(db, link)
        db.commit()

    def list_medication_members(
        self,
        db: Session,
        membership: FamilyMembership,
        medication_id: int,
    ) -> MedicationMemberListResponse:
        medication = self._get_scoped_medication(db, membership, medication_id)
        members = self.repository.list_medication_members(db, medication.id)
        return MedicationMemberListResponse(
            items=[MedicationMemberResponse.model_validate(m) for m in members]
        )

    def list_member_medications(
        self,
        db: Session,
        membership: FamilyMembership,
        member_id: int,
        *,
        include_archived: bool = False,
    ) -> MedicationListResponse:
        member = self._get_scoped_member(db, membership, member_id)
        rows = self.repository.list_member_medications(
            db,
            family_id=membership.family_id,
            member_id=member.id,
            include_archived=include_archived,
        )
        return MedicationListResponse(
            items=[MedicationResponse.from_model(row) for row in rows]
        )

    # ------------------------------------------------------------------
    # Internal Helpers & Guards
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_active_status(
        *,
        quantity: float,
        expiration_date: date | None,
    ) -> str:
        if quantity <= 0:
            return MedicationStatus.DEPLETED.value
        if expiration_date is not None and expiration_date < date.today():
            return MedicationStatus.EXPIRED.value
        return MedicationStatus.ACTIVE.value

    def _get_scoped_medication(
        self,
        db: Session,
        membership: FamilyMembership,
        medication_id: int,
    ) -> FamilyMedication:
        medication = self.repository.get_family_medication(
            db,
            family_id=membership.family_id,
            medication_id=medication_id,
        )
        if medication is None:
            raise MedicationNotFoundError("Medication not found")
        return medication

    def _get_scoped_member(
        self,
        db: Session,
        membership: FamilyMembership,
        member_id: int,
    ) -> FamilyMember:
        member = self.member_repository.get_member(
            db,
            family_id=membership.family_id,
            member_id=member_id,
        )
        if member is None:
            raise MemberNotFoundError("Member not found")
        return member

    @staticmethod
    def _ensure_roles(
        membership: FamilyMembership,
        *allowed_roles: FamilyRole,
    ) -> None:
        allowed_values = {role.value for role in allowed_roles}
        if membership.role not in allowed_values:
            raise InsufficientFamilyPermissionError(
                "Insufficient family permission"
            )

    @staticmethod
    def _ensure_family_active(family: Family) -> None:
        if family.status != FamilyStatus.ACTIVE.value:
            raise FamilyArchivedError("Family archived")

    @staticmethod
    def _ensure_medication_not_archived(medication: FamilyMedication) -> None:
        if medication.status == MedicationStatus.ARCHIVED.value:
            raise MedicationArchivedError("Medication archived")

    @staticmethod
    def _ensure_member_active(member: FamilyMember) -> None:
        if member.status != MemberStatus.ACTIVE.value:
            raise MemberArchivedError("Member archived")
