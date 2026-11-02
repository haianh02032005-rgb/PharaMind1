from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from backend.app.api.dependencies import get_db
from backend.app.core.exceptions import AppException
from backend.app.models.family_membership import FamilyMembership
from backend.app.modules.families.dependencies import (
    get_family_membership,
    require_family_roles,
)
from backend.app.modules.medications.enums import MedicationStatus
from backend.app.modules.medications.schema import (
    InventoryUpdateRequest,
    MedicationCreateRequest,
    MedicationListResponse,
    MedicationMemberLinkRequest,
    MedicationMemberListResponse,
    MedicationMemberResponse,
    MedicationResponse,
    MedicationUpdateRequest,
)
from backend.app.modules.medications.service import MedicationService
from backend.app.shared.enums import FamilyRole


router = APIRouter()

WRITE_ROLES = (
    FamilyRole.OWNER,
    FamilyRole.ADMIN,
    FamilyRole.CAREGIVER,
)

ADMIN_ROLES = (
    FamilyRole.OWNER,
    FamilyRole.ADMIN,
)


def get_medication_service() -> MedicationService:
    return MedicationService()


def _raise_http_from_app_error(exc: AppException) -> None:
    raise HTTPException(
        status_code=exc.status_code,
        detail=exc.detail,
    ) from exc


@router.post(
    "",
    response_model=MedicationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_medication(
    payload: MedicationCreateRequest,
    membership: FamilyMembership = Depends(require_family_roles(*WRITE_ROLES)),
    db: Session = Depends(get_db),
    service: MedicationService = Depends(get_medication_service),
) -> MedicationResponse:
    try:
        return service.create_medication(db, membership, payload)
    except AppException as exc:
        _raise_http_from_app_error(exc)


@router.get(
    "",
    response_model=MedicationListResponse,
    status_code=status.HTTP_200_OK,
)
def list_medications(
    status_filter: MedicationStatus | None = Query(default=None, alias="status"),
    search: str | None = Query(default=None),
    include_archived: bool = Query(default=False),
    membership: FamilyMembership = Depends(get_family_membership),
    db: Session = Depends(get_db),
    service: MedicationService = Depends(get_medication_service),
) -> MedicationListResponse:
    try:
        return service.list_medications(
            db,
            membership,
            status=status_filter,
            search=search,
            include_archived=include_archived,
        )
    except AppException as exc:
        _raise_http_from_app_error(exc)


@router.get(
    "/{medication_id}",
    response_model=MedicationResponse,
    status_code=status.HTTP_200_OK,
)
def get_medication(
    medication_id: int,
    membership: FamilyMembership = Depends(get_family_membership),
    db: Session = Depends(get_db),
    service: MedicationService = Depends(get_medication_service),
) -> MedicationResponse:
    try:
        return service.get_medication_detail(db, membership, medication_id)
    except AppException as exc:
        _raise_http_from_app_error(exc)


@router.patch(
    "/{medication_id}",
    response_model=MedicationResponse,
    status_code=status.HTTP_200_OK,
)
def update_medication(
    medication_id: int,
    payload: MedicationUpdateRequest,
    membership: FamilyMembership = Depends(require_family_roles(*WRITE_ROLES)),
    db: Session = Depends(get_db),
    service: MedicationService = Depends(get_medication_service),
) -> MedicationResponse:
    try:
        return service.update_medication(
            db, membership, medication_id, payload
        )
    except AppException as exc:
        _raise_http_from_app_error(exc)


@router.patch(
    "/{medication_id}/inventory",
    response_model=MedicationResponse,
    status_code=status.HTTP_200_OK,
)
def update_medication_inventory(
    medication_id: int,
    payload: InventoryUpdateRequest,
    membership: FamilyMembership = Depends(require_family_roles(*WRITE_ROLES)),
    db: Session = Depends(get_db),
    service: MedicationService = Depends(get_medication_service),
) -> MedicationResponse:
    try:
        return service.update_inventory(db, membership, medication_id, payload)
    except AppException as exc:
        _raise_http_from_app_error(exc)


@router.post(
    "/{medication_id}/archive",
    response_model=MedicationResponse,
    status_code=status.HTTP_200_OK,
)
def archive_medication(
    medication_id: int,
    membership: FamilyMembership = Depends(require_family_roles(*ADMIN_ROLES)),
    db: Session = Depends(get_db),
    service: MedicationService = Depends(get_medication_service),
) -> MedicationResponse:
    try:
        return service.archive_medication(db, membership, medication_id)
    except AppException as exc:
        _raise_http_from_app_error(exc)


@router.post(
    "/{medication_id}/restore",
    response_model=MedicationResponse,
    status_code=status.HTTP_200_OK,
)
def restore_medication(
    medication_id: int,
    membership: FamilyMembership = Depends(require_family_roles(*ADMIN_ROLES)),
    db: Session = Depends(get_db),
    service: MedicationService = Depends(get_medication_service),
) -> MedicationResponse:
    try:
        return service.restore_medication(db, membership, medication_id)
    except AppException as exc:
        _raise_http_from_app_error(exc)


@router.get(
    "/{medication_id}/members",
    response_model=MedicationMemberListResponse,
    status_code=status.HTTP_200_OK,
)
def list_medication_members(
    medication_id: int,
    membership: FamilyMembership = Depends(get_family_membership),
    db: Session = Depends(get_db),
    service: MedicationService = Depends(get_medication_service),
) -> MedicationMemberListResponse:
    try:
        return service.list_medication_members(db, membership, medication_id)
    except AppException as exc:
        _raise_http_from_app_error(exc)


@router.post(
    "/{medication_id}/members",
    response_model=MedicationMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
def link_medication_member(
    medication_id: int,
    payload: MedicationMemberLinkRequest,
    membership: FamilyMembership = Depends(require_family_roles(*WRITE_ROLES)),
    db: Session = Depends(get_db),
    service: MedicationService = Depends(get_medication_service),
) -> MedicationMemberResponse:
    try:
        return service.link_member(db, membership, medication_id, payload)
    except AppException as exc:
        _raise_http_from_app_error(exc)


@router.delete(
    "/{medication_id}/members/{member_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def unlink_medication_member(
    medication_id: int,
    member_id: int,
    membership: FamilyMembership = Depends(require_family_roles(*WRITE_ROLES)),
    db: Session = Depends(get_db),
    service: MedicationService = Depends(get_medication_service),
) -> Response:
    try:
        service.unlink_member(db, membership, medication_id, member_id)
    except AppException as exc:
        _raise_http_from_app_error(exc)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
