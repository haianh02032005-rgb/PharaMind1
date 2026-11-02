from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.api.dependencies import get_db
from backend.app.models.family_membership import FamilyMembership
from backend.app.models.prescription import Prescription
from backend.app.modules.families.dependencies import get_family_membership
from backend.app.modules.prescriptions.repository import PrescriptionRepository


def get_family_prescription(
    family_id: int,
    prescription_id: int,
    membership: FamilyMembership = Depends(get_family_membership),
    db: Session = Depends(get_db),
) -> Prescription:
    prescription = PrescriptionRepository().get_prescription(
        db,
        family_id=membership.family_id,
        prescription_id=prescription_id,
    )
    if prescription is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prescription not found",
        )
    return prescription
