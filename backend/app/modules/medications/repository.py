from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from backend.app.models.family_medication import FamilyMedication
from backend.app.models.family_member import FamilyMember
from backend.app.models.medication_catalog import MedicationCatalog
from backend.app.models.member_medication import MemberMedication
from backend.app.modules.medications.enums import MedicationStatus


class MedicationRepository:
    # ------------------------------------------------------------------
    # MedicationCatalog Persistence
    # ------------------------------------------------------------------

    def find_catalog(
        self,
        db: Session,
        *,
        name: str,
        active_ingredient: str | None = None,
        strength: str | None = None,
        dosage_form: str | None = None,
        manufacturer: str | None = None,
    ) -> MedicationCatalog | None:
        stmt = select(MedicationCatalog).where(
            func.lower(MedicationCatalog.name) == name.strip().lower()
        )

        if active_ingredient is None:
            stmt = stmt.where(MedicationCatalog.active_ingredient.is_(None))
        else:
            stmt = stmt.where(
                func.lower(MedicationCatalog.active_ingredient)
                == active_ingredient.strip().lower()
            )

        if strength is None:
            stmt = stmt.where(MedicationCatalog.strength.is_(None))
        else:
            stmt = stmt.where(
                func.lower(MedicationCatalog.strength)
                == strength.strip().lower()
            )

        if dosage_form is None:
            stmt = stmt.where(MedicationCatalog.dosage_form.is_(None))
        else:
            stmt = stmt.where(MedicationCatalog.dosage_form == dosage_form)

        if manufacturer is None:
            stmt = stmt.where(MedicationCatalog.manufacturer.is_(None))
        else:
            stmt = stmt.where(
                func.lower(MedicationCatalog.manufacturer)
                == manufacturer.strip().lower()
            )

        return db.scalar(stmt)

    def create_catalog(
        self,
        db: Session,
        catalog: MedicationCatalog,
    ) -> MedicationCatalog:
        db.add(catalog)
        db.flush()
        return catalog

    # ------------------------------------------------------------------
    # FamilyMedication Persistence
    # ------------------------------------------------------------------

    def create_family_medication(
        self,
        db: Session,
        medication: FamilyMedication,
    ) -> FamilyMedication:
        db.add(medication)
        db.flush()
        return medication

    def get_family_medication(
        self,
        db: Session,
        *,
        family_id: int,
        medication_id: int,
    ) -> FamilyMedication | None:
        stmt = select(FamilyMedication).where(
            FamilyMedication.id == medication_id,
            FamilyMedication.family_id == family_id,
        )
        return db.scalar(stmt)

    def list_family_medications(
        self,
        db: Session,
        *,
        family_id: int,
        status: str | None = None,
        search: str | None = None,
        include_archived: bool = False,
    ) -> list[FamilyMedication]:
        stmt = (
            select(FamilyMedication)
            .join(
                MedicationCatalog,
                MedicationCatalog.id == FamilyMedication.catalog_id,
            )
            .where(FamilyMedication.family_id == family_id)
        )

        if status is not None:
            stmt = stmt.where(FamilyMedication.status == status)
        elif not include_archived:
            stmt = stmt.where(
                FamilyMedication.status != MedicationStatus.ARCHIVED.value
            )

        if search is not None and search.strip():
            pattern = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    MedicationCatalog.name.ilike(pattern),
                    MedicationCatalog.active_ingredient.ilike(pattern),
                    MedicationCatalog.manufacturer.ilike(pattern),
                )
            )

        stmt = stmt.order_by(FamilyMedication.id.asc())
        return list(db.scalars(stmt).unique().all())

    def update_family_medication(
        self,
        db: Session,
        medication: FamilyMedication,
        **changes: Any,
    ) -> FamilyMedication:
        for field_name, value in changes.items():
            setattr(medication, field_name, value)
        db.add(medication)
        db.flush()
        return medication

    def archive_medication(
        self,
        db: Session,
        medication: FamilyMedication,
    ) -> FamilyMedication:
        medication.status = MedicationStatus.ARCHIVED.value
        db.add(medication)
        db.flush()
        return medication

    def restore_medication(
        self,
        db: Session,
        medication: FamilyMedication,
        restored_status: str,
    ) -> FamilyMedication:
        medication.status = restored_status
        db.add(medication)
        db.flush()
        return medication

    # ------------------------------------------------------------------
    # MemberMedication Persistence
    # ------------------------------------------------------------------

    def get_member_link(
        self,
        db: Session,
        *,
        member_id: int,
        family_medication_id: int,
    ) -> MemberMedication | None:
        stmt = select(MemberMedication).where(
            MemberMedication.member_id == member_id,
            MemberMedication.family_medication_id == family_medication_id,
        )
        return db.scalar(stmt)

    def create_member_link(
        self,
        db: Session,
        link: MemberMedication,
    ) -> MemberMedication:
        db.add(link)
        db.flush()
        return link

    def delete_member_link(
        self,
        db: Session,
        link: MemberMedication,
    ) -> None:
        db.delete(link)
        db.flush()

    def list_medication_members(
        self,
        db: Session,
        family_medication_id: int,
    ) -> list[FamilyMember]:
        stmt = (
            select(FamilyMember)
            .join(
                MemberMedication,
                MemberMedication.member_id == FamilyMember.id,
            )
            .where(
                MemberMedication.family_medication_id == family_medication_id
            )
            .order_by(FamilyMember.id.asc())
        )
        return list(db.scalars(stmt).unique().all())

    def list_member_medications(
        self,
        db: Session,
        *,
        family_id: int,
        member_id: int,
        include_archived: bool = False,
    ) -> list[FamilyMedication]:
        stmt = (
            select(FamilyMedication)
            .join(
                MemberMedication,
                MemberMedication.family_medication_id == FamilyMedication.id,
            )
            .where(
                FamilyMedication.family_id == family_id,
                MemberMedication.member_id == member_id,
            )
        )
        if not include_archived:
            stmt = stmt.where(
                FamilyMedication.status != MedicationStatus.ARCHIVED.value
            )
        stmt = stmt.order_by(FamilyMedication.id.asc())
        return list(db.scalars(stmt).unique().all())
