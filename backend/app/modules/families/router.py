from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from backend.app.api.dependencies import get_db
from backend.app.core.exceptions import AppException
from backend.app.models.family_membership import FamilyMembership
from backend.app.models.user import User
from backend.app.modules.auth.dependencies import get_current_user
from backend.app.modules.families.dependencies import (
    get_family_membership,
    require_family_roles,
)
from backend.app.modules.families.schema import (
    FamilyCreateRequest,
    FamilyListResponse,
    FamilyMembershipCreateRequest,
    FamilyMembershipListResponse,
    FamilyMembershipResponse,
    FamilyMembershipUpdateRequest,
    FamilyResponse,
    FamilyUpdateRequest,
)
from backend.app.modules.families.service import FamilyService
from backend.app.shared.enums import FamilyRole


router = APIRouter()


def get_family_service() -> FamilyService:
    return FamilyService()


@router.post(
    "",
    response_model=FamilyResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_family(
    payload: FamilyCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    service: FamilyService = Depends(get_family_service),
) -> FamilyResponse:
    try:
        return service.create_family(db, current_user, payload)
    except AppException as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.detail,
        ) from exc


@router.get(
    "",
    response_model=FamilyListResponse,
    status_code=status.HTTP_200_OK,
)
def list_families(
    include_archived: bool = Query(default=False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    service: FamilyService = Depends(get_family_service),
) -> FamilyListResponse:
    return service.list_my_families(
        db,
        current_user,
        include_archived=include_archived,
    )


@router.get(
    "/{family_id}",
    response_model=FamilyResponse,
    status_code=status.HTTP_200_OK,
)
def get_family(
    membership: FamilyMembership = Depends(get_family_membership),
    service: FamilyService = Depends(get_family_service),
) -> FamilyResponse:
    return service.get_family_detail(membership)


@router.patch(
    "/{family_id}",
    response_model=FamilyResponse,
    status_code=status.HTTP_200_OK,
)
def update_family(
    payload: FamilyUpdateRequest,
    membership: FamilyMembership = Depends(
        require_family_roles(FamilyRole.OWNER, FamilyRole.ADMIN)
    ),
    db: Session = Depends(get_db),
    service: FamilyService = Depends(get_family_service),
) -> FamilyResponse:
    try:
        return service.update_family(db, membership, payload)
    except AppException as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.detail,
        ) from exc


@router.post(
    "/{family_id}/archive",
    response_model=FamilyResponse,
    status_code=status.HTTP_200_OK,
)
def archive_family(
    membership: FamilyMembership = Depends(require_family_roles(FamilyRole.OWNER)),
    db: Session = Depends(get_db),
    service: FamilyService = Depends(get_family_service),
) -> FamilyResponse:
    try:
        return service.archive_family(db, membership)
    except AppException as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.detail,
        ) from exc


@router.post(
    "/{family_id}/restore",
    response_model=FamilyResponse,
    status_code=status.HTTP_200_OK,
)
def restore_family(
    membership: FamilyMembership = Depends(require_family_roles(FamilyRole.OWNER)),
    db: Session = Depends(get_db),
    service: FamilyService = Depends(get_family_service),
) -> FamilyResponse:
    try:
        return service.restore_family(db, membership)
    except AppException as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.detail,
        ) from exc


@router.get(
    "/{family_id}/memberships",
    response_model=FamilyMembershipListResponse,
    status_code=status.HTTP_200_OK,
)
def list_memberships(
    membership: FamilyMembership = Depends(get_family_membership),
    db: Session = Depends(get_db),
    service: FamilyService = Depends(get_family_service),
) -> FamilyMembershipListResponse:
    return service.list_memberships(db, membership)


@router.post(
    "/{family_id}/memberships",
    response_model=FamilyMembershipResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_membership(
    payload: FamilyMembershipCreateRequest,
    membership: FamilyMembership = Depends(
        require_family_roles(FamilyRole.OWNER, FamilyRole.ADMIN)
    ),
    db: Session = Depends(get_db),
    service: FamilyService = Depends(get_family_service),
) -> FamilyMembershipResponse:
    try:
        return service.add_membership(db, membership, payload)
    except AppException as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.detail,
        ) from exc


@router.patch(
    "/{family_id}/memberships/{membership_id}",
    response_model=FamilyMembershipResponse,
    status_code=status.HTTP_200_OK,
)
def update_membership_role(
    membership_id: int,
    payload: FamilyMembershipUpdateRequest,
    membership: FamilyMembership = Depends(require_family_roles(FamilyRole.OWNER)),
    db: Session = Depends(get_db),
    service: FamilyService = Depends(get_family_service),
) -> FamilyMembershipResponse:
    try:
        return service.update_membership_role(db, membership, membership_id, payload)
    except AppException as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.detail,
        ) from exc


@router.delete(
    "/{family_id}/memberships/{membership_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_membership(
    membership_id: int,
    membership: FamilyMembership = Depends(
        require_family_roles(FamilyRole.OWNER, FamilyRole.ADMIN)
    ),
    db: Session = Depends(get_db),
    service: FamilyService = Depends(get_family_service),
) -> Response:
    try:
        service.remove_membership(db, membership, membership_id)
    except AppException as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.detail,
        ) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
