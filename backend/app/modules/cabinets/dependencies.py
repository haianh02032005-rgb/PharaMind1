from fastapi import Depends
from sqlalchemy.orm import Session

from backend.app.api.dependencies import get_db
from backend.app.models.cabinet import Cabinet
from backend.app.models.family_membership import FamilyMembership
from backend.app.modules.cabinets.exceptions import CabinetNotFoundError
from backend.app.modules.cabinets.repository import CabinetRepository
from backend.app.modules.cabinets.service import CabinetService
from backend.app.modules.families.dependencies import get_family_membership


def get_cabinet_repository() -> CabinetRepository:
    return CabinetRepository()


def get_cabinet_service() -> CabinetService:
    return CabinetService()


def get_scoped_cabinet(
    cabinet_id: int,
    membership: FamilyMembership = Depends(get_family_membership),
    db: Session = Depends(get_db),
    repository: CabinetRepository = Depends(get_cabinet_repository),
) -> Cabinet:
    cabinet = repository.get_cabinet(
        db,
        family_id=membership.family_id,
        cabinet_id=cabinet_id,
    )
    if cabinet is None:
        raise CabinetNotFoundError("Cabinet not found")
    return cabinet
