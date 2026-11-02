from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.prescription import Prescription
from backend.app.models.prescription_item import PrescriptionItem
from backend.app.modules.prescriptions.enums import PrescriptionStatus


class PrescriptionRepository:
    # ------------------------------------------------------------------
    # Prescription Persistence
    # ------------------------------------------------------------------

    def create_prescription(
        self,
        db: Session,
        prescription: Prescription,
    ) -> Prescription:
        db.add(prescription)
        db.flush()
        return prescription

    def get_prescription(
        self,
        db: Session,
        *,
        family_id: int,
        prescription_id: int,
    ) -> Prescription | None:
        stmt = select(Prescription).where(
            Prescription.id == prescription_id,
            Prescription.family_id == family_id,
        )
        return db.scalar(stmt)

    def list_prescriptions(
        self,
        db: Session,
        *,
        family_id: int,
        member_id: int | None = None,
        status: str | None = None,
        include_archived: bool = False,
    ) -> list[Prescription]:
        stmt = select(Prescription).where(Prescription.family_id == family_id)

        if member_id is not None:
            stmt = stmt.where(Prescription.member_id == member_id)

        if status is not None:
            stmt = stmt.where(Prescription.status == status)
        elif not include_archived:
            stmt = stmt.where(
                Prescription.status != PrescriptionStatus.ARCHIVED.value
            )

        stmt = stmt.order_by(Prescription.id.asc())
        return list(db.scalars(stmt).unique().all())

    def update_prescription(
        self,
        db: Session,
        prescription: Prescription,
        **changes: Any,
    ) -> Prescription:
        for field_name, value in changes.items():
            setattr(prescription, field_name, value)
        db.add(prescription)
        db.flush()
        return prescription

    def complete_prescription(
        self,
        db: Session,
        prescription: Prescription,
    ) -> Prescription:
        prescription.status = PrescriptionStatus.COMPLETED.value
        db.add(prescription)
        db.flush()
        return prescription

    def archive_prescription(
        self,
        db: Session,
        prescription: Prescription,
    ) -> Prescription:
        prescription.status = PrescriptionStatus.ARCHIVED.value
        db.add(prescription)
        db.flush()
        return prescription

    def restore_prescription(
        self,
        db: Session,
        prescription: Prescription,
    ) -> Prescription:
        prescription.status = PrescriptionStatus.ACTIVE.value
        db.add(prescription)
        db.flush()
        return prescription

    # ------------------------------------------------------------------
    # PrescriptionItem Persistence
    # ------------------------------------------------------------------

    def get_item_by_medication(
        self,
        db: Session,
        *,
        prescription_id: int,
        family_medication_id: int,
    ) -> PrescriptionItem | None:
        stmt = select(PrescriptionItem).where(
            PrescriptionItem.prescription_id == prescription_id,
            PrescriptionItem.family_medication_id == family_medication_id,
        )
        return db.scalar(stmt)

    def get_item(
        self,
        db: Session,
        *,
        prescription_id: int,
        item_id: int,
    ) -> PrescriptionItem | None:
        stmt = select(PrescriptionItem).where(
            PrescriptionItem.id == item_id,
            PrescriptionItem.prescription_id == prescription_id,
        )
        return db.scalar(stmt)

    def create_item(
        self,
        db: Session,
        item: PrescriptionItem,
    ) -> PrescriptionItem:
        db.add(item)
        db.flush()
        return item

    def update_item(
        self,
        db: Session,
        item: PrescriptionItem,
        **changes: Any,
    ) -> PrescriptionItem:
        for field_name, value in changes.items():
            setattr(item, field_name, value)
        db.add(item)
        db.flush()
        return item

    def delete_item(
        self,
        db: Session,
        item: PrescriptionItem,
    ) -> None:
        db.delete(item)
        db.flush()
