from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.api.dependencies import get_db
from backend.app.models.family_medication import FamilyMedication
from backend.app.models.family_membership import FamilyMembership
from backend.app.modules.families.dependencies import get_family_membership
from backend.app.modules.medications.repository import MedicationRepository


def get_family_medication(
    family_id: int,
    medication_id: int,
    membership: FamilyMembership = Depends(get_family_membership),
    db: Session = Depends(get_db),
) -> FamilyMedication:
    medication = MedicationRepository().get_family_medication(
        db,
        family_id=membership.family_id,
        medication_id=medication_id,
    )
    if medication is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medication not found",
        )
    return medication
