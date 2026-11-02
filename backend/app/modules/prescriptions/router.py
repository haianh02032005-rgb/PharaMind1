from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from backend.app.api.dependencies import get_db
from backend.app.core.exceptions import AppException
from backend.app.models.family_membership import FamilyMembership
from backend.app.modules.families.dependencies import (
    get_family_membership,
    require_family_roles,
)
from backend.app.modules.prescriptions.enums import PrescriptionStatus
from backend.app.modules.prescriptions.schema import (
    PrescriptionCreateRequest,
    PrescriptionItemCreateRequest,
    PrescriptionItemResponse,
    PrescriptionItemUpdateRequest,
    PrescriptionListResponse,
    PrescriptionResponse,
    PrescriptionUpdateRequest,
)
from backend.app.modules.prescriptions.service import PrescriptionService
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


def get_prescription_service() -> PrescriptionService:
    return PrescriptionService()


def _raise_http_from_app_error(exc: AppException) -> None:
    raise HTTPException(
        status_code=exc.status_code,
        detail=exc.detail,
    ) from exc


@router.post(
    "",
    response_model=PrescriptionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_prescription(
    payload: PrescriptionCreateRequest,
    membership: FamilyMembership = Depends(require_family_roles(*WRITE_ROLES)),
    db: Session = Depends(get_db),
    service: PrescriptionService = Depends(get_prescription_service),
) -> PrescriptionResponse:
    try:
        return service.create_prescription(db, membership, payload)
    except AppException as exc:
        _raise_http_from_app_error(exc)


@router.get(
    "",
    response_model=PrescriptionListResponse,
    status_code=status.HTTP_200_OK,
)
def list_prescriptions(
    member_id: int | None = Query(default=None),
    status_filter: PrescriptionStatus | None = Query(default=None, alias="status"),
    include_archived: bool = Query(default=False),
    membership: FamilyMembership = Depends(get_family_membership),
    db: Session = Depends(get_db),
    service: PrescriptionService = Depends(get_prescription_service),
) -> PrescriptionListResponse:
    try:
        return service.list_prescriptions(
            db,
            membership,
            member_id=member_id,
            status=status_filter,
            include_archived=include_archived,
        )
    except AppException as exc:
        _raise_http_from_app_error(exc)


@router.get(
    "/{prescription_id}",
    response_model=PrescriptionResponse,
    status_code=status.HTTP_200_OK,
)
def get_prescription(
    prescription_id: int,
    membership: FamilyMembership = Depends(get_family_membership),
    db: Session = Depends(get_db),
    service: PrescriptionService = Depends(get_prescription_service),
) -> PrescriptionResponse:
    try:
        return service.get_prescription_detail(db, membership, prescription_id)
    except AppException as exc:
        _raise_http_from_app_error(exc)


@router.patch(
    "/{prescription_id}",
    response_model=PrescriptionResponse,
    status_code=status.HTTP_200_OK,
)
def update_prescription(
    prescription_id: int,
    payload: PrescriptionUpdateRequest,
    membership: FamilyMembership = Depends(require_family_roles(*WRITE_ROLES)),
    db: Session = Depends(get_db),
    service: PrescriptionService = Depends(get_prescription_service),
) -> PrescriptionResponse:
    try:
        return service.update_prescription(
            db, membership, prescription_id, payload
        )
    except AppException as exc:
        _raise_http_from_app_error(exc)


@router.post(
    "/{prescription_id}/complete",
    response_model=PrescriptionResponse,
    status_code=status.HTTP_200_OK,
)
def complete_prescription(
    prescription_id: int,
    membership: FamilyMembership = Depends(require_family_roles(*WRITE_ROLES)),
    db: Session = Depends(get_db),
    service: PrescriptionService = Depends(get_prescription_service),
) -> PrescriptionResponse:
    try:
        return service.complete_prescription(db, membership, prescription_id)
    except AppException as exc:
        _raise_http_from_app_error(exc)


@router.post(
    "/{prescription_id}/archive",
    response_model=PrescriptionResponse,
    status_code=status.HTTP_200_OK,
)
def archive_prescription(
    prescription_id: int,
    membership: FamilyMembership = Depends(require_family_roles(*ADMIN_ROLES)),
    db: Session = Depends(get_db),
    service: PrescriptionService = Depends(get_prescription_service),
) -> PrescriptionResponse:
    try:
        return service.archive_prescription(db, membership, prescription_id)
    except AppException as exc:
        _raise_http_from_app_error(exc)


@router.post(
    "/{prescription_id}/restore",
    response_model=PrescriptionResponse,
    status_code=status.HTTP_200_OK,
)
def restore_prescription(
    prescription_id: int,
    membership: FamilyMembership = Depends(require_family_roles(*ADMIN_ROLES)),
    db: Session = Depends(get_db),
    service: PrescriptionService = Depends(get_prescription_service),
) -> PrescriptionResponse:
    try:
        return service.restore_prescription(db, membership, prescription_id)
    except AppException as exc:
        _raise_http_from_app_error(exc)


@router.post(
    "/{prescription_id}/items",
    response_model=PrescriptionItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_prescription_item(
    prescription_id: int,
    payload: PrescriptionItemCreateRequest,
    membership: FamilyMembership = Depends(require_family_roles(*WRITE_ROLES)),
    db: Session = Depends(get_db),
    service: PrescriptionService = Depends(get_prescription_service),
) -> PrescriptionItemResponse:
    try:
        return service.add_item(db, membership, prescription_id, payload)
    except AppException as exc:
        _raise_http_from_app_error(exc)


@router.patch(
    "/{prescription_id}/items/{item_id}",
    response_model=PrescriptionItemResponse,
    status_code=status.HTTP_200_OK,
)
def update_prescription_item(
    prescription_id: int,
    item_id: int,
    payload: PrescriptionItemUpdateRequest,
    membership: FamilyMembership = Depends(require_family_roles(*WRITE_ROLES)),
    db: Session = Depends(get_db),
    service: PrescriptionService = Depends(get_prescription_service),
) -> PrescriptionItemResponse:
    try:
        return service.update_item(
            db, membership, prescription_id, item_id, payload
        )
    except AppException as exc:
        _raise_http_from_app_error(exc)


@router.delete(
    "/{prescription_id}/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_prescription_item(
    prescription_id: int,
    item_id: int,
    membership: FamilyMembership = Depends(require_family_roles(*WRITE_ROLES)),
    db: Session = Depends(get_db),
    service: PrescriptionService = Depends(get_prescription_service),
) -> Response:
    try:
        service.delete_item(db, membership, prescription_id, item_id)
    except AppException as exc:
        _raise_http_from_app_error(exc)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
