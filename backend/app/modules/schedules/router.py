from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.api.dependencies import get_db
from backend.app.core.exceptions import AppException
from backend.app.models.family_membership import FamilyMembership
from backend.app.modules.families.dependencies import (
    get_family_membership,
    require_family_roles,
)
from backend.app.modules.schedules.dependencies import get_schedule_service
from backend.app.modules.schedules.enums import ScheduleStatus
from backend.app.modules.schedules.schema import (
    MedicationScheduleCreateRequest,
    MedicationScheduleListResponse,
    MedicationScheduleResponse,
    MedicationScheduleUpdateRequest,
)
from backend.app.modules.schedules.service import (
    ADMIN_SCHEDULE_ROLES,
    WRITE_SCHEDULE_ROLES,
    ScheduleService,
)


router = APIRouter()


def _raise_http_from_app_error(exc: AppException) -> None:
    raise HTTPException(
        status_code=exc.status_code,
        detail=exc.detail,
    ) from exc


@router.post(
    "",
    response_model=MedicationScheduleResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_schedule(
    payload: MedicationScheduleCreateRequest,
    membership: FamilyMembership = Depends(
        require_family_roles(*WRITE_SCHEDULE_ROLES)
    ),
    db: Session = Depends(get_db),
    service: ScheduleService = Depends(get_schedule_service),
) -> MedicationScheduleResponse:
    try:
        return service.create_schedule(db, membership, payload)
    except AppException as exc:
        _raise_http_from_app_error(exc)


@router.get(
    "",
    response_model=MedicationScheduleListResponse,
    status_code=status.HTTP_200_OK,
)
def list_schedules(
    member_id: int | None = Query(default=None),
    status_filter: ScheduleStatus | None = Query(default=None, alias="status"),
    target_date: date | None = Query(default=None, alias="date"),
    medication_id: int | None = Query(default=None),
    include_archived: bool = Query(default=False),
    membership: FamilyMembership = Depends(get_family_membership),
    db: Session = Depends(get_db),
    service: ScheduleService = Depends(get_schedule_service),
) -> MedicationScheduleListResponse:
    try:
        return service.list_schedules(
            db,
            membership,
            member_id=member_id,
            status=status_filter,
            target_date=target_date,
            medication_id=medication_id,
            include_archived=include_archived,
        )
    except AppException as exc:
        _raise_http_from_app_error(exc)


@router.get(
    "/{schedule_id}",
    response_model=MedicationScheduleResponse,
    status_code=status.HTTP_200_OK,
)
def get_schedule(
    schedule_id: int,
    membership: FamilyMembership = Depends(get_family_membership),
    db: Session = Depends(get_db),
    service: ScheduleService = Depends(get_schedule_service),
) -> MedicationScheduleResponse:
    try:
        return service.get_schedule_detail(db, membership, schedule_id)
    except AppException as exc:
        _raise_http_from_app_error(exc)


@router.patch(
    "/{schedule_id}",
    response_model=MedicationScheduleResponse,
    status_code=status.HTTP_200_OK,
)
def update_schedule(
    schedule_id: int,
    payload: MedicationScheduleUpdateRequest,
    membership: FamilyMembership = Depends(
        require_family_roles(*WRITE_SCHEDULE_ROLES)
    ),
    db: Session = Depends(get_db),
    service: ScheduleService = Depends(get_schedule_service),
) -> MedicationScheduleResponse:
    try:
        return service.update_schedule(db, membership, schedule_id, payload)
    except AppException as exc:
        _raise_http_from_app_error(exc)


@router.post(
    "/{schedule_id}/pause",
    response_model=MedicationScheduleResponse,
    status_code=status.HTTP_200_OK,
)
def pause_schedule(
    schedule_id: int,
    membership: FamilyMembership = Depends(
        require_family_roles(*WRITE_SCHEDULE_ROLES)
    ),
    db: Session = Depends(get_db),
    service: ScheduleService = Depends(get_schedule_service),
) -> MedicationScheduleResponse:
    try:
        return service.pause_schedule(db, membership, schedule_id)
    except AppException as exc:
        _raise_http_from_app_error(exc)


@router.post(
    "/{schedule_id}/resume",
    response_model=MedicationScheduleResponse,
    status_code=status.HTTP_200_OK,
)
def resume_schedule(
    schedule_id: int,
    membership: FamilyMembership = Depends(
        require_family_roles(*WRITE_SCHEDULE_ROLES)
    ),
    db: Session = Depends(get_db),
    service: ScheduleService = Depends(get_schedule_service),
) -> MedicationScheduleResponse:
    try:
        return service.resume_schedule(db, membership, schedule_id)
    except AppException as exc:
        _raise_http_from_app_error(exc)


@router.post(
    "/{schedule_id}/complete",
    response_model=MedicationScheduleResponse,
    status_code=status.HTTP_200_OK,
)
def complete_schedule(
    schedule_id: int,
    membership: FamilyMembership = Depends(
        require_family_roles(*WRITE_SCHEDULE_ROLES)
    ),
    db: Session = Depends(get_db),
    service: ScheduleService = Depends(get_schedule_service),
) -> MedicationScheduleResponse:
    try:
        return service.complete_schedule(db, membership, schedule_id)
    except AppException as exc:
        _raise_http_from_app_error(exc)


@router.post(
    "/{schedule_id}/archive",
    response_model=MedicationScheduleResponse,
    status_code=status.HTTP_200_OK,
)
def archive_schedule(
    schedule_id: int,
    membership: FamilyMembership = Depends(
        require_family_roles(*ADMIN_SCHEDULE_ROLES)
    ),
    db: Session = Depends(get_db),
    service: ScheduleService = Depends(get_schedule_service),
) -> MedicationScheduleResponse:
    try:
        return service.archive_schedule(db, membership, schedule_id)
    except AppException as exc:
        _raise_http_from_app_error(exc)


@router.post(
    "/{schedule_id}/restore",
    response_model=MedicationScheduleResponse,
    status_code=status.HTTP_200_OK,
)
def restore_schedule(
    schedule_id: int,
    membership: FamilyMembership = Depends(
        require_family_roles(*ADMIN_SCHEDULE_ROLES)
    ),
    db: Session = Depends(get_db),
    service: ScheduleService = Depends(get_schedule_service),
) -> MedicationScheduleResponse:
    try:
        return service.restore_schedule(db, membership, schedule_id)
    except AppException as exc:
        _raise_http_from_app_error(exc)
