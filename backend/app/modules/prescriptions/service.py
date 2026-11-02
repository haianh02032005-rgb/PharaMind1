from typing import Any

from sqlalchemy.orm import Session

from backend.app.models.family import Family
from backend.app.models.family_medication import FamilyMedication
from backend.app.models.family_member import FamilyMember
from backend.app.models.family_membership import FamilyMembership
from backend.app.models.prescription import Prescription
from backend.app.models.prescription_item import PrescriptionItem
from backend.app.modules.families.exceptions import (
    FamilyArchivedError,
    InsufficientFamilyPermissionError,
)
from backend.app.modules.medications.enums import MedicationStatus
from backend.app.modules.medications.exceptions import (
    MedicationArchivedError,
    MedicationNotFoundError,
)
from backend.app.modules.medications.repository import MedicationRepository
from backend.app.modules.members.exceptions import (
    MemberArchivedError,
    MemberNotFoundError,
)
from backend.app.modules.members.repository import MemberRepository
from backend.app.modules.prescriptions.enums import PrescriptionStatus
from backend.app.modules.prescriptions.exceptions import (
    DuplicatePrescriptionItemError,
    InvalidPrescriptionDateRangeError,
    MedicationNotLinkedToMemberError,
    PrescriptionArchivedError,
    PrescriptionCompletedError,
    PrescriptionItemNotFoundError,
    PrescriptionNotFoundError,
)
from backend.app.modules.prescriptions.repository import PrescriptionRepository
from backend.app.modules.prescriptions.schema import (
    PrescriptionCreateRequest,
    PrescriptionItemCreateRequest,
    PrescriptionItemResponse,
    PrescriptionItemUpdateRequest,
    PrescriptionListResponse,
    PrescriptionResponse,
    PrescriptionUpdateRequest,
)
from backend.app.shared.enums import FamilyRole, FamilyStatus, MemberStatus


WRITE_PRESCRIPTION_ROLES = (
    FamilyRole.OWNER,
    FamilyRole.ADMIN,
    FamilyRole.CAREGIVER,
)

ADMIN_PRESCRIPTION_ROLES = (
    FamilyRole.OWNER,
    FamilyRole.ADMIN,
)


class PrescriptionService:
    def __init__(
        self,
        repository: PrescriptionRepository | None = None,
        member_repository: MemberRepository | None = None,
        medication_repository: MedicationRepository | None = None,
    ) -> None:
        self.repository = repository or PrescriptionRepository()
        self.member_repository = member_repository or MemberRepository()
        self.medication_repository = (
            medication_repository or MedicationRepository()
        )

    # ------------------------------------------------------------------
    # Prescription Operations
    # ------------------------------------------------------------------

    def create_prescription(
        self,
        db: Session,
        membership: FamilyMembership,
        payload: PrescriptionCreateRequest,
    ) -> PrescriptionResponse:
        self._ensure_roles(membership, *WRITE_PRESCRIPTION_ROLES)
        self._ensure_family_active(membership.family)

        member = self._get_scoped_member(db, membership, payload.member_id)
        self._ensure_member_active(member)

        prescription = Prescription(
            family_id=membership.family_id,
            member_id=member.id,
            title=payload.title,
            doctor_name=payload.doctor_name,
            facility_name=payload.facility_name,
            issued_at=payload.issued_at,
            start_date=payload.start_date,
            end_date=payload.end_date,
            status=payload.status.value,
            notes=payload.notes,
        )
        created = self.repository.create_prescription(db, prescription)
        db.commit()
        db.refresh(created)
        return PrescriptionResponse.from_model(created)

    def list_prescriptions(
        self,
        db: Session,
        membership: FamilyMembership,
        *,
        member_id: int | None = None,
        status: PrescriptionStatus | None = None,
        include_archived: bool = False,
    ) -> PrescriptionListResponse:
        if member_id is not None:
            self._get_scoped_member(db, membership, member_id)

        rows = self.repository.list_prescriptions(
            db,
            family_id=membership.family_id,
            member_id=member_id,
            status=status.value if status is not None else None,
            include_archived=include_archived,
        )
        return PrescriptionListResponse(
            items=[PrescriptionResponse.from_model(row) for row in rows]
        )

    def list_member_prescriptions(
        self,
        db: Session,
        membership: FamilyMembership,
        member_id: int,
        *,
        include_archived: bool = False,
    ) -> PrescriptionListResponse:
        member = self._get_scoped_member(db, membership, member_id)
        rows = self.repository.list_prescriptions(
            db,
            family_id=membership.family_id,
            member_id=member.id,
            include_archived=include_archived,
        )
        return PrescriptionListResponse(
            items=[PrescriptionResponse.from_model(row) for row in rows]
        )

    def get_prescription_detail(
        self,
        db: Session,
        membership: FamilyMembership,
        prescription_id: int,
    ) -> PrescriptionResponse:
        prescription = self._get_scoped_prescription(
            db, membership, prescription_id
        )
        return PrescriptionResponse.from_model(prescription)

    def update_prescription(
        self,
        db: Session,
        membership: FamilyMembership,
        prescription_id: int,
        payload: PrescriptionUpdateRequest,
    ) -> PrescriptionResponse:
        self._ensure_roles(membership, *WRITE_PRESCRIPTION_ROLES)
        self._ensure_family_active(membership.family)

        prescription = self._get_scoped_prescription(
            db, membership, prescription_id
        )
        self._ensure_prescription_editable(prescription)

        changes: dict[str, Any] = {}
        for field_name in payload.model_fields_set:
            value = getattr(payload, field_name)
            if field_name == "status" and value is not None:
                value = value.value
            changes[field_name] = value

        effective_start = changes.get("start_date", prescription.start_date)
        effective_end = changes.get("end_date", prescription.end_date)
        if (
            effective_start is not None
            and effective_end is not None
            and effective_start > effective_end
        ):
            raise InvalidPrescriptionDateRangeError(
                "start_date cannot be after end_date"
            )

        if changes:
            prescription = self.repository.update_prescription(
                db, prescription, **changes
            )
            db.commit()
            db.refresh(prescription)

        return PrescriptionResponse.from_model(prescription)

    def complete_prescription(
        self,
        db: Session,
        membership: FamilyMembership,
        prescription_id: int,
    ) -> PrescriptionResponse:
        self._ensure_roles(membership, *WRITE_PRESCRIPTION_ROLES)
        self._ensure_family_active(membership.family)

        prescription = self._get_scoped_prescription(
            db, membership, prescription_id
        )
        if prescription.status == PrescriptionStatus.ARCHIVED.value:
            raise PrescriptionArchivedError("Prescription is archived")

        updated = self.repository.complete_prescription(db, prescription)
        db.commit()
        db.refresh(updated)
        return PrescriptionResponse.from_model(updated)

    def archive_prescription(
        self,
        db: Session,
        membership: FamilyMembership,
        prescription_id: int,
    ) -> PrescriptionResponse:
        self._ensure_roles(membership, *ADMIN_PRESCRIPTION_ROLES)
        self._ensure_family_active(membership.family)

        prescription = self._get_scoped_prescription(
            db, membership, prescription_id
        )
        updated = self.repository.archive_prescription(db, prescription)
        db.commit()
        db.refresh(updated)
        return PrescriptionResponse.from_model(updated)

    def restore_prescription(
        self,
        db: Session,
        membership: FamilyMembership,
        prescription_id: int,
    ) -> PrescriptionResponse:
        self._ensure_roles(membership, *ADMIN_PRESCRIPTION_ROLES)
        self._ensure_family_active(membership.family)

        prescription = self._get_scoped_prescription(
            db, membership, prescription_id
        )
        updated = self.repository.restore_prescription(db, prescription)
        db.commit()
        db.refresh(updated)
        return PrescriptionResponse.from_model(updated)

    # ------------------------------------------------------------------
    # PrescriptionItem Operations
    # ------------------------------------------------------------------

    def add_item(
        self,
        db: Session,
        membership: FamilyMembership,
        prescription_id: int,
        payload: PrescriptionItemCreateRequest,
    ) -> PrescriptionItemResponse:
        self._ensure_roles(membership, *WRITE_PRESCRIPTION_ROLES)
        self._ensure_family_active(membership.family)

        prescription = self._get_scoped_prescription(
            db, membership, prescription_id
        )
        self._ensure_prescription_editable(prescription)

        member = self._get_scoped_member(db, membership, prescription.member_id)
        self._ensure_member_active(member)

        medication = self._get_scoped_medication(
            db, membership, payload.family_medication_id
        )
        self._ensure_medication_not_archived(medication)

        # TASK 07 §19 (Option A), §42, §54: Medication must be linked to Member
        member_link = self.medication_repository.get_member_link(
            db,
            member_id=prescription.member_id,
            family_medication_id=medication.id,
        )
        if member_link is None:
            raise MedicationNotLinkedToMemberError(
                "Medication must be linked to the member before adding to prescription"
            )

        # TASK 07 §21, §55: Prevent duplicate medication in same prescription
        existing_item = self.repository.get_item_by_medication(
            db,
            prescription_id=prescription.id,
            family_medication_id=medication.id,
        )
        if existing_item is not None:
            raise DuplicatePrescriptionItemError(
                "Medication is already added to this prescription"
            )

        item = PrescriptionItem(
            prescription_id=prescription.id,
            family_medication_id=medication.id,
            dose_amount=payload.dose_amount,
            dose_unit=(
                payload.dose_unit.value
                if payload.dose_unit is not None
                else None
            ),
            frequency_per_day=payload.frequency_per_day,
            frequency_text=payload.frequency_text,
            route=(
                payload.route.value if payload.route is not None else None
            ),
            instructions=payload.instructions,
        )
        created = self.repository.create_item(db, item)
        db.commit()
        db.refresh(created)
        return PrescriptionItemResponse.from_model(created)

    def update_item(
        self,
        db: Session,
        membership: FamilyMembership,
        prescription_id: int,
        item_id: int,
        payload: PrescriptionItemUpdateRequest,
    ) -> PrescriptionItemResponse:
        self._ensure_roles(membership, *WRITE_PRESCRIPTION_ROLES)
        self._ensure_family_active(membership.family)

        prescription = self._get_scoped_prescription(
            db, membership, prescription_id
        )
        self._ensure_prescription_editable(prescription)

        item = self.repository.get_item(
            db, prescription_id=prescription.id, item_id=item_id
        )
        if item is None:
            raise PrescriptionItemNotFoundError("Prescription item not found")

        changes: dict[str, Any] = {}
        for field_name in payload.model_fields_set:
            value = getattr(payload, field_name)
            if field_name in {"dose_unit", "route"} and value is not None:
                value = value.value
            changes[field_name] = value

        if changes:
            item = self.repository.update_item(db, item, **changes)
            db.commit()
            db.refresh(item)

        return PrescriptionItemResponse.from_model(item)

    def delete_item(
        self,
        db: Session,
        membership: FamilyMembership,
        prescription_id: int,
        item_id: int,
    ) -> None:
        self._ensure_roles(membership, *WRITE_PRESCRIPTION_ROLES)
        self._ensure_family_active(membership.family)

        prescription = self._get_scoped_prescription(
            db, membership, prescription_id
        )
        self._ensure_prescription_editable(prescription)

        item = self.repository.get_item(
            db, prescription_id=prescription.id, item_id=item_id
        )
        if item is None:
            raise PrescriptionItemNotFoundError("Prescription item not found")

        self.repository.delete_item(db, item)
        db.commit()

    # ------------------------------------------------------------------
    # Internal Guards
    # ------------------------------------------------------------------

    def _get_scoped_prescription(
        self,
        db: Session,
        membership: FamilyMembership,
        prescription_id: int,
    ) -> Prescription:
        prescription = self.repository.get_prescription(
            db,
            family_id=membership.family_id,
            prescription_id=prescription_id,
        )
        if prescription is None:
            raise PrescriptionNotFoundError("Prescription not found")
        return prescription

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

    def _get_scoped_medication(
        self,
        db: Session,
        membership: FamilyMembership,
        medication_id: int,
    ) -> FamilyMedication:
        medication = self.medication_repository.get_family_medication(
            db,
            family_id=membership.family_id,
            medication_id=medication_id,
        )
        if medication is None:
            raise MedicationNotFoundError("Medication not found")
        return medication

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
    def _ensure_member_active(member: FamilyMember) -> None:
        if member.status != MemberStatus.ACTIVE.value:
            raise MemberArchivedError("Member archived")

    @staticmethod
    def _ensure_medication_not_archived(medication: FamilyMedication) -> None:
        if medication.status == MedicationStatus.ARCHIVED.value:
            raise MedicationArchivedError("Medication archived")

    @staticmethod
    def _ensure_prescription_editable(prescription: Prescription) -> None:
        if prescription.status == PrescriptionStatus.ARCHIVED.value:
            raise PrescriptionArchivedError("Prescription is archived")
        if prescription.status == PrescriptionStatus.COMPLETED.value:
            raise PrescriptionCompletedError(
                "Completed prescription cannot be modified"
            )
