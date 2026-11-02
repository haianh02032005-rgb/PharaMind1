from typing import Any

from sqlalchemy import select, update
from sqlalchemy.orm import Session, joinedload

from backend.app.models.allergy_profile import AllergyProfile
from backend.app.models.drug_reaction_history import DrugReactionHistory
from backend.app.models.emergency_contact import EmergencyContact
from backend.app.models.family_member import FamilyMember
from backend.app.models.health_profile import HealthProfile
from backend.app.models.medical_condition import MedicalCondition
from backend.app.shared.enums import MemberStatus


class MemberRepository:
    # ------------------------------------------------------------------
    # FamilyMember
    # ------------------------------------------------------------------

    def create_member(
        self,
        db: Session,
        member: FamilyMember,
    ) -> FamilyMember:
        db.add(member)
        db.flush()
        db.refresh(member)
        return member

    def get_member(
        self,
        db: Session,
        *,
        family_id: int,
        member_id: int,
    ) -> FamilyMember | None:
        stmt = (
            select(FamilyMember)
            .options(joinedload(FamilyMember.health_profile))
            .where(
                FamilyMember.id == member_id,
                FamilyMember.family_id == family_id,
            )
        )
        return db.execute(stmt).scalar_one_or_none()

    def list_members(
        self,
        db: Session,
        *,
        family_id: int,
        include_archived: bool = False,
    ) -> list[FamilyMember]:
        stmt = select(FamilyMember).where(FamilyMember.family_id == family_id)
        if not include_archived:
            stmt = stmt.where(FamilyMember.status == MemberStatus.ACTIVE.value)
        stmt = stmt.order_by(FamilyMember.id.asc())
        return list(db.execute(stmt).scalars().all())

    def update_member(
        self,
        db: Session,
        member: FamilyMember,
        **changes: Any,
    ) -> FamilyMember:
        for field_name, value in changes.items():
            setattr(member, field_name, value)
        db.add(member)
        db.flush()
        db.refresh(member)
        return member

    def archive_member(
        self,
        db: Session,
        member: FamilyMember,
    ) -> FamilyMember:
        member.status = MemberStatus.ARCHIVED.value
        db.add(member)
        db.flush()
        db.refresh(member)
        return member

    def restore_member(
        self,
        db: Session,
        member: FamilyMember,
    ) -> FamilyMember:
        member.status = MemberStatus.ACTIVE.value
        db.add(member)
        db.flush()
        db.refresh(member)
        return member

    # ------------------------------------------------------------------
    # HealthProfile
    # ------------------------------------------------------------------

    def create_health_profile(
        self,
        db: Session,
        profile: HealthProfile,
    ) -> HealthProfile:
        db.add(profile)
        db.flush()
        db.refresh(profile)
        return profile

    def get_health_profile(
        self,
        db: Session,
        member_id: int,
    ) -> HealthProfile | None:
        stmt = select(HealthProfile).where(HealthProfile.member_id == member_id)
        return db.execute(stmt).scalar_one_or_none()

    def update_health_profile(
        self,
        db: Session,
        profile: HealthProfile,
        **changes: Any,
    ) -> HealthProfile:
        for field_name, value in changes.items():
            setattr(profile, field_name, value)
        db.add(profile)
        db.flush()
        db.refresh(profile)
        return profile

    # ------------------------------------------------------------------
    # MedicalCondition
    # ------------------------------------------------------------------

    def list_conditions(
        self,
        db: Session,
        member_id: int,
    ) -> list[MedicalCondition]:
        stmt = (
            select(MedicalCondition)
            .where(MedicalCondition.member_id == member_id)
            .order_by(MedicalCondition.id.asc())
        )
        return list(db.execute(stmt).scalars().all())

    def get_condition(
        self,
        db: Session,
        *,
        member_id: int,
        condition_id: int,
    ) -> MedicalCondition | None:
        stmt = select(MedicalCondition).where(
            MedicalCondition.id == condition_id,
            MedicalCondition.member_id == member_id,
        )
        return db.execute(stmt).scalar_one_or_none()

    def create_condition(
        self,
        db: Session,
        condition: MedicalCondition,
    ) -> MedicalCondition:
        db.add(condition)
        db.flush()
        db.refresh(condition)
        return condition

    def update_condition(
        self,
        db: Session,
        condition: MedicalCondition,
        **changes: Any,
    ) -> MedicalCondition:
        for field_name, value in changes.items():
            setattr(condition, field_name, value)
        db.add(condition)
        db.flush()
        db.refresh(condition)
        return condition

    def delete_condition(
        self,
        db: Session,
        condition: MedicalCondition,
    ) -> None:
        db.delete(condition)
        db.flush()

    # ------------------------------------------------------------------
    # AllergyProfile
    # ------------------------------------------------------------------

    def list_allergies(
        self,
        db: Session,
        member_id: int,
    ) -> list[AllergyProfile]:
        stmt = (
            select(AllergyProfile)
            .where(AllergyProfile.member_id == member_id)
            .order_by(AllergyProfile.id.asc())
        )
        return list(db.execute(stmt).scalars().all())

    def get_allergy(
        self,
        db: Session,
        *,
        member_id: int,
        allergy_id: int,
    ) -> AllergyProfile | None:
        stmt = select(AllergyProfile).where(
            AllergyProfile.id == allergy_id,
            AllergyProfile.member_id == member_id,
        )
        return db.execute(stmt).scalar_one_or_none()

    def create_allergy(
        self,
        db: Session,
        allergy: AllergyProfile,
    ) -> AllergyProfile:
        db.add(allergy)
        db.flush()
        db.refresh(allergy)
        return allergy

    def update_allergy(
        self,
        db: Session,
        allergy: AllergyProfile,
        **changes: Any,
    ) -> AllergyProfile:
        for field_name, value in changes.items():
            setattr(allergy, field_name, value)
        db.add(allergy)
        db.flush()
        db.refresh(allergy)
        return allergy

    def delete_allergy(
        self,
        db: Session,
        allergy: AllergyProfile,
    ) -> None:
        db.delete(allergy)
        db.flush()

    # ------------------------------------------------------------------
    # DrugReactionHistory
    # ------------------------------------------------------------------

    def list_drug_reactions(
        self,
        db: Session,
        member_id: int,
    ) -> list[DrugReactionHistory]:
        stmt = (
            select(DrugReactionHistory)
            .where(DrugReactionHistory.member_id == member_id)
            .order_by(DrugReactionHistory.id.asc())
        )
        return list(db.execute(stmt).scalars().all())

    def get_drug_reaction(
        self,
        db: Session,
        *,
        member_id: int,
        reaction_id: int,
    ) -> DrugReactionHistory | None:
        stmt = select(DrugReactionHistory).where(
            DrugReactionHistory.id == reaction_id,
            DrugReactionHistory.member_id == member_id,
        )
        return db.execute(stmt).scalar_one_or_none()

    def create_drug_reaction(
        self,
        db: Session,
        reaction: DrugReactionHistory,
    ) -> DrugReactionHistory:
        db.add(reaction)
        db.flush()
        db.refresh(reaction)
        return reaction

    def update_drug_reaction(
        self,
        db: Session,
        reaction: DrugReactionHistory,
        **changes: Any,
    ) -> DrugReactionHistory:
        for field_name, value in changes.items():
            setattr(reaction, field_name, value)
        db.add(reaction)
        db.flush()
        db.refresh(reaction)
        return reaction

    def delete_drug_reaction(
        self,
        db: Session,
        reaction: DrugReactionHistory,
    ) -> None:
        db.delete(reaction)
        db.flush()

    # ------------------------------------------------------------------
    # EmergencyContact
    # ------------------------------------------------------------------

    def list_emergency_contacts(
        self,
        db: Session,
        member_id: int,
    ) -> list[EmergencyContact]:
        stmt = (
            select(EmergencyContact)
            .where(EmergencyContact.member_id == member_id)
            .order_by(EmergencyContact.id.asc())
        )
        return list(db.execute(stmt).scalars().all())

    def get_emergency_contact(
        self,
        db: Session,
        *,
        member_id: int,
        contact_id: int,
    ) -> EmergencyContact | None:
        stmt = select(EmergencyContact).where(
            EmergencyContact.id == contact_id,
            EmergencyContact.member_id == member_id,
        )
        return db.execute(stmt).scalar_one_or_none()

    def clear_primary_emergency_contacts(
        self,
        db: Session,
        member_id: int,
        *,
        exclude_id: int | None = None,
    ) -> None:
        stmt = (
            update(EmergencyContact)
            .where(
                EmergencyContact.member_id == member_id,
                EmergencyContact.is_primary.is_(True),
            )
            .values(is_primary=False)
        )
        if exclude_id is not None:
            stmt = stmt.where(EmergencyContact.id != exclude_id)
        db.execute(stmt)
        db.flush()

    def create_emergency_contact(
        self,
        db: Session,
        contact: EmergencyContact,
    ) -> EmergencyContact:
        db.add(contact)
        db.flush()
        db.refresh(contact)
        return contact

    def update_emergency_contact(
        self,
        db: Session,
        contact: EmergencyContact,
        **changes: Any,
    ) -> EmergencyContact:
        for field_name, value in changes.items():
            setattr(contact, field_name, value)
        db.add(contact)
        db.flush()
        db.refresh(contact)
        return contact

    def delete_emergency_contact(
        self,
        db: Session,
        contact: EmergencyContact,
    ) -> None:
        db.delete(contact)
        db.flush()
