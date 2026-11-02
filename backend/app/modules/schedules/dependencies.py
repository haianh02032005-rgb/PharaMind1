from fastapi import Depends
from sqlalchemy.orm import Session

from backend.app.api.dependencies import get_db
from backend.app.models.family_membership import FamilyMembership
from backend.app.models.medication_schedule import MedicationSchedule
from backend.app.modules.families.dependencies import get_family_membership
from backend.app.modules.schedules.exceptions import ScheduleNotFoundError
from backend.app.modules.schedules.repository import ScheduleRepository
from backend.app.modules.schedules.service import ScheduleService


def get_schedule_repository() -> ScheduleRepository:
    return ScheduleRepository()


def get_schedule_service() -> ScheduleService:
    return ScheduleService()


def get_scoped_schedule(
    schedule_id: int,
    membership: FamilyMembership = Depends(get_family_membership),
    db: Session = Depends(get_db),
    repository: ScheduleRepository = Depends(get_schedule_repository),
) -> MedicationSchedule:
    schedule = repository.get_schedule(
        db,
        family_id=membership.family_id,
        schedule_id=schedule_id,
    )
    if schedule is None:
        raise ScheduleNotFoundError("Schedule not found")
    return schedule
