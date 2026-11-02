from typing import Any

from sqlalchemy.orm import Session

from backend.app.models.allergy_profile import AllergyProfile
from backend.app.models.drug_reaction_history import DrugReactionHistory
from backend.app.models.emergency_contact import EmergencyContact
from backend.app.models.family import Family
from backend.app.models.family_member import FamilyMember
from backend.app.models.family_membership import FamilyMembership
from backend.app.models.health_profile import HealthProfile
from backend.app.models.medical_condition import MedicalCondition
from backend.app.modules.families.exceptions import (
    FamilyArchivedError,
    InsufficientFamilyPermissionError,
)
from backend.app.modules.members.exceptions import (
    AllergyNotFoundError,
    DrugReactionNotFoundError,
    EmergencyContactNotFoundError,
    HealthProfileNotFoundError,
    MedicalConditionNotFoundError,
    MemberArchivedError,
    MemberNotFoundError,
)
from backend.app.modules.members.repository import MemberRepository
from backend.app.modules.members.schema import (
    AllergyCreateRequest,
    AllergyListResponse,
    AllergyResponse,
    AllergyUpdateRequest,
    DrugReactionCreateRequest,
    DrugReactionListResponse,
    DrugReactionResponse,
    DrugReactionUpdateRequest,
    EmergencyContactCreateRequest,
    EmergencyContactListResponse,
    EmergencyContactResponse,
    EmergencyContactUpdateRequest,
    HealthProfileResponse,
    HealthProfileUpdateRequest,
    MedicalConditionCreateRequest,
    MedicalConditionListResponse,
    MedicalConditionResponse,
    MedicalConditionUpdateRequest,
    MemberCreateRequest,
    MemberListItem,
    MemberListResponse,
    MemberResponse,
    MemberUpdateRequest,
)
from backend.app.shared.enums import FamilyRole, FamilyStatus, MemberStatus


WRITE_MEMBER_ROLES = (
    FamilyRole.OWNER,
    FamilyRole.ADMIN,
    FamilyRole.CAREGIVER,
)

ADMIN_MEMBER_ROLES = (
    FamilyRole.OWNER,
    FamilyRole.ADMIN,
)


class MemberService:
    def __init__(self, repository: MemberRepository | None = None) -> None:
        self.repository = repository or MemberRepository()

    # ------------------------------------------------------------------
    # FamilyMember Operations
    # ------------------------------------------------------------------

    def create_member(
        self,
        db: Session,
        membership: FamilyMembership,
        payload: MemberCreateRequest,
    ) -> MemberResponse:
        self._ensure_roles(membership, *WRITE_MEMBER_ROLES)
        self._ensure_family_active(membership.family)

        member = FamilyMember(
            family_id=membership.family_id,
            full_name=payload.full_name,
            date_of_birth=payload.date_of_birth,
            gender=payload.gender.value if payload.gender is not None else None,
            relationship_label=payload.relationship_label,
            avatar_url=payload.avatar_url,
            status=MemberStatus.ACTIVE.value,
        )

        try:
            created_member = self.repository.create_member(db, member)
            health_profile = HealthProfile(member_id=created_member.id)
            self.repository.create_health_profile(db, health_profile)
            db.commit()
            db.refresh(created_member)
        except Exception:
            db.rollback()
            raise

        return MemberResponse.model_validate(created_member)

    def list_members(
        self,
        db: Session,
        membership: FamilyMembership,
        *,
        include_archived: bool = False,
    ) -> MemberListResponse:
        rows = self.repository.list_members(
            db,
            family_id=membership.family_id,
            include_archived=include_archived,
        )
        items = [MemberListItem.model_validate(row) for row in rows]
        return MemberListResponse(items=items)

    def get_member_detail(
        self,
        db: Session,
        membership: FamilyMembership,
        member_id: int,
    ) -> MemberResponse:
        member = self._get_scoped_member(db, membership, member_id)
        return MemberResponse.model_validate(member)

    def update_member(
        self,
        db: Session,
        membership: FamilyMembership,
        member_id: int,
        payload: MemberUpdateRequest,
    ) -> MemberResponse:
        self._ensure_roles(membership, *WRITE_MEMBER_ROLES)
        self._ensure_family_active(membership.family)

        member = self._get_scoped_member(db, membership, member_id)
        self._ensure_member_active(member)

        changes: dict[str, Any] = {}
        for field_name in payload.model_fields_set:
            value = getattr(payload, field_name)
            if field_name == "gender" and value is not None:
                value = value.value
            changes[field_name] = value

        if changes:
            member = self.repository.update_member(db, member, **changes)
            db.commit()
            db.refresh(member)

        return MemberResponse.model_validate(member)

    def archive_member(
        self,
        db: Session,
        membership: FamilyMembership,
        member_id: int,
    ) -> MemberResponse:
        self._ensure_roles(membership, *ADMIN_MEMBER_ROLES)
        self._ensure_family_active(membership.family)

        member = self._get_scoped_member(db, membership, member_id)
        updated = self.repository.archive_member(db, member)
        db.commit()
        db.refresh(updated)
        return MemberResponse.model_validate(updated)

    def restore_member(
        self,
        db: Session,
        membership: FamilyMembership,
        member_id: int,
    ) -> MemberResponse:
        self._ensure_roles(membership, *ADMIN_MEMBER_ROLES)
        self._ensure_family_active(membership.family)

        member = self._get_scoped_member(db, membership, member_id)
        updated = self.repository.restore_member(db, member)
        db.commit()
        db.refresh(updated)
        return MemberResponse.model_validate(updated)

    # ------------------------------------------------------------------
    # HealthProfile Operations
    # ------------------------------------------------------------------

    def get_health_profile(
        self,
        db: Session,
        membership: FamilyMembership,
        member_id: int,
    ) -> HealthProfileResponse:
        member = self._get_scoped_member(db, membership, member_id)
        profile = member.health_profile or self.repository.get_health_profile(
            db, member.id
        )
        if profile is None:
            raise HealthProfileNotFoundError("Health profile not found")
        return HealthProfileResponse.model_validate(profile)

    def update_health_profile(
        self,
        db: Session,
        membership: FamilyMembership,
        member_id: int,
        payload: HealthProfileUpdateRequest,
    ) -> HealthProfileResponse:
        self._ensure_roles(membership, *WRITE_MEMBER_ROLES)
        self._ensure_family_active(membership.family)

        member = self._get_scoped_member(db, membership, member_id)
        self._ensure_member_active(member)

        profile = member.health_profile or self.repository.get_health_profile(
            db, member.id
        )
        if profile is None:
            raise HealthProfileNotFoundError("Health profile not found")

        changes: dict[str, Any] = {}
        for field_name in payload.model_fields_set:
            value = getattr(payload, field_name)
            if field_name == "blood_type" and value is not None:
                value = value.value
            changes[field_name] = value

        if changes:
            profile = self.repository.update_health_profile(
                db, profile, **changes
            )
            db.commit()
            db.refresh(profile)

        return HealthProfileResponse.model_validate(profile)

    # ------------------------------------------------------------------
    # MedicalCondition Operations
    # ------------------------------------------------------------------

    def list_conditions(
        self,
        db: Session,
        membership: FamilyMembership,
        member_id: int,
    ) -> MedicalConditionListResponse:
        member = self._get_scoped_member(db, membership, member_id)
        rows = self.repository.list_conditions(db, member.id)
        return MedicalConditionListResponse(
            items=[MedicalConditionResponse.model_validate(r) for r in rows]
        )

    def create_condition(
        self,
        db: Session,
        membership: FamilyMembership,
        member_id: int,
        payload: MedicalConditionCreateRequest,
    ) -> MedicalConditionResponse:
        self._ensure_roles(membership, *WRITE_MEMBER_ROLES)
        self._ensure_family_active(membership.family)

        member = self._get_scoped_member(db, membership, member_id)
        self._ensure_member_active(member)

        condition = MedicalCondition(
            member_id=member.id,
            name=payload.name,
            diagnosed_at=payload.diagnosed_at,
            status=payload.status.value,
            notes=payload.notes,
        )
        created = self.repository.create_condition(db, condition)
        db.commit()
        db.refresh(created)
        return MedicalConditionResponse.model_validate(created)

    def update_condition(
        self,
        db: Session,
        membership: FamilyMembership,
        member_id: int,
        condition_id: int,
        payload: MedicalConditionUpdateRequest,
    ) -> MedicalConditionResponse:
        self._ensure_roles(membership, *WRITE_MEMBER_ROLES)
        self._ensure_family_active(membership.family)

        member = self._get_scoped_member(db, membership, member_id)
        self._ensure_member_active(member)

        condition = self.repository.get_condition(
            db, member_id=member.id, condition_id=condition_id
        )
        if condition is None:
            raise MedicalConditionNotFoundError("Medical condition not found")

        changes: dict[str, Any] = {}
        for field_name in payload.model_fields_set:
            value = getattr(payload, field_name)
            if field_name == "status" and value is not None:
                value = value.value
            changes[field_name] = value

        if changes:
            condition = self.repository.update_condition(
                db, condition, **changes
            )
            db.commit()
            db.refresh(condition)

        return MedicalConditionResponse.model_validate(condition)

    def delete_condition(
        self,
        db: Session,
        membership: FamilyMembership,
        member_id: int,
        condition_id: int,
    ) -> None:
        self._ensure_roles(membership, *WRITE_MEMBER_ROLES)
        self._ensure_family_active(membership.family)

        member = self._get_scoped_member(db, membership, member_id)
        self._ensure_member_active(member)

        condition = self.repository.get_condition(
            db, member_id=member.id, condition_id=condition_id
        )
        if condition is None:
            raise MedicalConditionNotFoundError("Medical condition not found")

        self.repository.delete_condition(db, condition)
        db.commit()

    # ------------------------------------------------------------------
    # AllergyProfile Operations
    # ------------------------------------------------------------------

    def list_allergies(
        self,
        db: Session,
        membership: FamilyMembership,
        member_id: int,
    ) -> AllergyListResponse:
        member = self._get_scoped_member(db, membership, member_id)
        rows = self.repository.list_allergies(db, member.id)
        return AllergyListResponse(
            items=[AllergyResponse.model_validate(r) for r in rows]
        )

    def create_allergy(
        self,
        db: Session,
        membership: FamilyMembership,
        member_id: int,
        payload: AllergyCreateRequest,
    ) -> AllergyResponse:
        self._ensure_roles(membership, *WRITE_MEMBER_ROLES)
        self._ensure_family_active(membership.family)

        member = self._get_scoped_member(db, membership, member_id)
        self._ensure_member_active(member)

        allergy = AllergyProfile(
            member_id=member.id,
            allergen=payload.allergen,
            allergy_type=payload.allergy_type.value,
            severity=payload.severity.value,
            reaction_description=payload.reaction_description,
            recorded_at=payload.recorded_at,
            source=payload.source,
            notes=payload.notes,
        )
        created = self.repository.create_allergy(db, allergy)
        db.commit()
        db.refresh(created)
        return AllergyResponse.model_validate(created)

    def update_allergy(
        self,
        db: Session,
        membership: FamilyMembership,
        member_id: int,
        allergy_id: int,
        payload: AllergyUpdateRequest,
    ) -> AllergyResponse:
        self._ensure_roles(membership, *WRITE_MEMBER_ROLES)
        self._ensure_family_active(membership.family)

        member = self._get_scoped_member(db, membership, member_id)
        self._ensure_member_active(member)

        allergy = self.repository.get_allergy(
            db, member_id=member.id, allergy_id=allergy_id
        )
        if allergy is None:
            raise AllergyNotFoundError("Allergy not found")

        changes: dict[str, Any] = {}
        for field_name in payload.model_fields_set:
            value = getattr(payload, field_name)
            if field_name in {"allergy_type", "severity"} and value is not None:
                value = value.value
            changes[field_name] = value

        if changes:
            allergy = self.repository.update_allergy(db, allergy, **changes)
            db.commit()
            db.refresh(allergy)

        return AllergyResponse.model_validate(allergy)

    def delete_allergy(
        self,
        db: Session,
        membership: FamilyMembership,
        member_id: int,
        allergy_id: int,
    ) -> None:
        self._ensure_roles(membership, *WRITE_MEMBER_ROLES)
        self._ensure_family_active(membership.family)

        member = self._get_scoped_member(db, membership, member_id)
        self._ensure_member_active(member)

        allergy = self.repository.get_allergy(
            db, member_id=member.id, allergy_id=allergy_id
        )
        if allergy is None:
            raise AllergyNotFoundError("Allergy not found")

        self.repository.delete_allergy(db, allergy)
        db.commit()

    # ------------------------------------------------------------------
    # DrugReactionHistory Operations
    # (Strictly separate from AllergyProfile - TASK 05 §21, §22)
    # ------------------------------------------------------------------

    def list_drug_reactions(
        self,
        db: Session,
        membership: FamilyMembership,
        member_id: int,
    ) -> DrugReactionListResponse:
        member = self._get_scoped_member(db, membership, member_id)
        rows = self.repository.list_drug_reactions(db, member.id)
        return DrugReactionListResponse(
            items=[DrugReactionResponse.model_validate(r) for r in rows]
        )

    def create_drug_reaction(
        self,
        db: Session,
        membership: FamilyMembership,
        member_id: int,
        payload: DrugReactionCreateRequest,
    ) -> DrugReactionResponse:
        self._ensure_roles(membership, *WRITE_MEMBER_ROLES)
        self._ensure_family_active(membership.family)

        member = self._get_scoped_member(db, membership, member_id)
        self._ensure_member_active(member)

        reaction = DrugReactionHistory(
            member_id=member.id,
            drug_name=payload.drug_name,
            active_ingredient=payload.active_ingredient,
            reaction=payload.reaction,
            severity=payload.severity.value,
            occurred_at=payload.occurred_at,
            confirmed_by_professional=payload.confirmed_by_professional,
            notes=payload.notes,
        )
        created = self.repository.create_drug_reaction(db, reaction)
        db.commit()
        db.refresh(created)
        return DrugReactionResponse.model_validate(created)

    def update_drug_reaction(
        self,
        db: Session,
        membership: FamilyMembership,
        member_id: int,
        reaction_id: int,
        payload: DrugReactionUpdateRequest,
    ) -> DrugReactionResponse:
        self._ensure_roles(membership, *WRITE_MEMBER_ROLES)
        self._ensure_family_active(membership.family)

        member = self._get_scoped_member(db, membership, member_id)
        self._ensure_member_active(member)

        reaction = self.repository.get_drug_reaction(
            db, member_id=member.id, reaction_id=reaction_id
        )
        if reaction is None:
            raise DrugReactionNotFoundError("Drug reaction not found")

        changes: dict[str, Any] = {}
        for field_name in payload.model_fields_set:
            value = getattr(payload, field_name)
            if field_name == "severity" and value is not None:
                value = value.value
            changes[field_name] = value

        if changes:
            reaction = self.repository.update_drug_reaction(
                db, reaction, **changes
            )
            db.commit()
            db.refresh(reaction)

        return DrugReactionResponse.model_validate(reaction)

    def delete_drug_reaction(
        self,
        db: Session,
        membership: FamilyMembership,
        member_id: int,
        reaction_id: int,
    ) -> None:
        self._ensure_roles(membership, *WRITE_MEMBER_ROLES)
        self._ensure_family_active(membership.family)

        member = self._get_scoped_member(db, membership, member_id)
        self._ensure_member_active(member)

        reaction = self.repository.get_drug_reaction(
            db, member_id=member.id, reaction_id=reaction_id
        )
        if reaction is None:
            raise DrugReactionNotFoundError("Drug reaction not found")

        self.repository.delete_drug_reaction(db, reaction)
        db.commit()

    # ------------------------------------------------------------------
    # EmergencyContact Operations
    # (At most 1 primary contact per member - TASK 05 §45)
    # ------------------------------------------------------------------

    def list_emergency_contacts(
        self,
        db: Session,
        membership: FamilyMembership,
        member_id: int,
    ) -> EmergencyContactListResponse:
        member = self._get_scoped_member(db, membership, member_id)
        rows = self.repository.list_emergency_contacts(db, member.id)
        return EmergencyContactListResponse(
            items=[EmergencyContactResponse.model_validate(r) for r in rows]
        )

    def create_emergency_contact(
        self,
        db: Session,
        membership: FamilyMembership,
        member_id: int,
        payload: EmergencyContactCreateRequest,
    ) -> EmergencyContactResponse:
        self._ensure_roles(membership, *WRITE_MEMBER_ROLES)
        self._ensure_family_active(membership.family)

        member = self._get_scoped_member(db, membership, member_id)
        self._ensure_member_active(member)

        try:
            if payload.is_primary:
                self.repository.clear_primary_emergency_contacts(db, member.id)

            contact = EmergencyContact(
                member_id=member.id,
                name=payload.name,
                relationship=payload.relationship,
                phone=payload.phone,
                is_primary=payload.is_primary,
            )
            created = self.repository.create_emergency_contact(db, contact)
            db.commit()
            db.refresh(created)
        except Exception:
            db.rollback()
            raise

        return EmergencyContactResponse.model_validate(created)

    def update_emergency_contact(
        self,
        db: Session,
        membership: FamilyMembership,
        member_id: int,
        contact_id: int,
        payload: EmergencyContactUpdateRequest,
    ) -> EmergencyContactResponse:
        self._ensure_roles(membership, *WRITE_MEMBER_ROLES)
        self._ensure_family_active(membership.family)

        member = self._get_scoped_member(db, membership, member_id)
        self._ensure_member_active(member)

        contact = self.repository.get_emergency_contact(
            db, member_id=member.id, contact_id=contact_id
        )
        if contact is None:
            raise EmergencyContactNotFoundError("Emergency contact not found")

        changes: dict[str, Any] = {
            field_name: getattr(payload, field_name)
            for field_name in payload.model_fields_set
        }

        try:
            if changes.get("is_primary") is True:
                self.repository.clear_primary_emergency_contacts(
                    db, member.id, exclude_id=contact.id
                )
            if changes:
                contact = self.repository.update_emergency_contact(
                    db, contact, **changes
                )
                db.commit()
                db.refresh(contact)
        except Exception:
            db.rollback()
            raise

        return EmergencyContactResponse.model_validate(contact)

    def delete_emergency_contact(
        self,
        db: Session,
        membership: FamilyMembership,
        member_id: int,
        contact_id: int,
    ) -> None:
        self._ensure_roles(membership, *WRITE_MEMBER_ROLES)
        self._ensure_family_active(membership.family)

        member = self._get_scoped_member(db, membership, member_id)
        self._ensure_member_active(member)

        contact = self.repository.get_emergency_contact(
            db, member_id=member.id, contact_id=contact_id
        )
        if contact is None:
            raise EmergencyContactNotFoundError("Emergency contact not found")

        self.repository.delete_emergency_contact(db, contact)
        db.commit()

    # ------------------------------------------------------------------
    # Internal Guards
    # ------------------------------------------------------------------

    def _get_scoped_member(
        self,
        db: Session,
        membership: FamilyMembership,
        member_id: int,
    ) -> FamilyMember:
        member = self.repository.get_member(
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
    def _ensure_member_active(member: FamilyMember) -> None:
        if member.status != MemberStatus.ACTIVE.value:
            raise MemberArchivedError("Member archived")
