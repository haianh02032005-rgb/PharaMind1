from datetime import datetime

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from sqlalchemy.orm import Session

from backend.app.api.dependencies import get_db
from backend.app.core.exceptions import AppException
from backend.app.core.security import decode_token
from backend.app.models.family_membership import FamilyMembership
from backend.app.modules.users.repository import UserRepository
from backend.app.modules.cabinets.dependencies import get_cabinet_service
from backend.app.modules.cabinets.enums import CabinetEventType
from backend.app.modules.cabinets.repository import CabinetRepository
from backend.app.modules.cabinets.schema import (
    CabinetCreateRequest,
    CabinetEventListResponse,
    CabinetListResponse,
    CabinetResponse,
    CabinetStateResponse,
    CompartmentDetailResponse,
    CompartmentListResponse,
    CompartmentResponse,
    CompartmentRevealResponse,
    DigitalTwinResponse,
    MedicationAssignmentRequest,
)
from backend.app.modules.cabinets.service import (
    ADMIN_CABINET_ROLES,
    WRITE_CABINET_ROLES,
    CabinetService,
)
from backend.app.modules.families.dependencies import (
    get_family_membership,
    require_family_roles,
)
from backend.app.modules.families.repository import FamilyRepository
from backend.app.realtime.websocket_manager import websocket_manager


router = APIRouter()
ws_router = APIRouter()


def _raise_http_from_app_error(exc: AppException) -> None:
    raise HTTPException(
        status_code=exc.status_code,
        detail=exc.detail,
    ) from exc


# ------------------------------------------------------------------
# Cabinet Endpoints
# ------------------------------------------------------------------


@router.post(
    "",
    response_model=CabinetResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_cabinet(
    payload: CabinetCreateRequest,
    membership: FamilyMembership = Depends(
        require_family_roles(*ADMIN_CABINET_ROLES)
    ),
    db: Session = Depends(get_db),
    service: CabinetService = Depends(get_cabinet_service),
) -> CabinetResponse:
    try:
        return await service.create_cabinet(db, membership, payload)
    except AppException as exc:
        _raise_http_from_app_error(exc)


@router.get(
    "",
    response_model=CabinetListResponse,
    status_code=status.HTTP_200_OK,
)
def list_cabinets(
    include_archived: bool = Query(default=False),
    membership: FamilyMembership = Depends(get_family_membership),
    db: Session = Depends(get_db),
    service: CabinetService = Depends(get_cabinet_service),
) -> CabinetListResponse:
    try:
        return service.list_cabinets(
            db,
            membership,
            include_archived=include_archived,
        )
    except AppException as exc:
        _raise_http_from_app_error(exc)


@router.get(
    "/{cabinet_id}",
    response_model=CabinetResponse,
    status_code=status.HTTP_200_OK,
)
def get_cabinet(
    cabinet_id: int,
    membership: FamilyMembership = Depends(get_family_membership),
    db: Session = Depends(get_db),
    service: CabinetService = Depends(get_cabinet_service),
) -> CabinetResponse:
    try:
        return service.get_cabinet_detail(db, membership, cabinet_id)
    except AppException as exc:
        _raise_http_from_app_error(exc)


@router.get(
    "/{cabinet_id}/state",
    response_model=CabinetStateResponse,
    status_code=status.HTTP_200_OK,
)
def get_cabinet_state(
    cabinet_id: int,
    membership: FamilyMembership = Depends(get_family_membership),
    db: Session = Depends(get_db),
    service: CabinetService = Depends(get_cabinet_service),
) -> CabinetStateResponse:
    try:
        return service.get_cabinet_state(db, membership, cabinet_id)
    except AppException as exc:
        _raise_http_from_app_error(exc)


@router.get(
    "/{cabinet_id}/digital-twin",
    response_model=DigitalTwinResponse,
    status_code=status.HTTP_200_OK,
)
def get_cabinet_digital_twin(
    cabinet_id: int,
    member_id: int | None = Query(default=None),
    membership: FamilyMembership = Depends(get_family_membership),
    db: Session = Depends(get_db),
    service: CabinetService = Depends(get_cabinet_service),
) -> DigitalTwinResponse:
    try:
        return service.get_digital_twin_summary(
            db,
            membership,
            cabinet_id,
            member_id=member_id,
        )
    except AppException as exc:
        _raise_http_from_app_error(exc)


@router.post(
    "/{cabinet_id}/archive",
    response_model=CabinetResponse,
    status_code=status.HTTP_200_OK,
)
def archive_cabinet(
    cabinet_id: int,
    membership: FamilyMembership = Depends(
        require_family_roles(*ADMIN_CABINET_ROLES)
    ),
    db: Session = Depends(get_db),
    service: CabinetService = Depends(get_cabinet_service),
) -> CabinetResponse:
    try:
        return service.archive_cabinet(db, membership, cabinet_id)
    except AppException as exc:
        _raise_http_from_app_error(exc)


# ------------------------------------------------------------------
# Compartment Endpoints
# ------------------------------------------------------------------


@router.get(
    "/{cabinet_id}/compartments",
    response_model=CompartmentListResponse,
    status_code=status.HTTP_200_OK,
)
def list_compartments(
    cabinet_id: int,
    membership: FamilyMembership = Depends(get_family_membership),
    db: Session = Depends(get_db),
    service: CabinetService = Depends(get_cabinet_service),
) -> CompartmentListResponse:
    try:
        return service.list_compartments(db, membership, cabinet_id)
    except AppException as exc:
        _raise_http_from_app_error(exc)


@router.get(
    "/{cabinet_id}/compartments/{position}",
    response_model=CompartmentDetailResponse,
    status_code=status.HTTP_200_OK,
)
def get_compartment_detail(
    cabinet_id: int,
    position: int,
    membership: FamilyMembership = Depends(get_family_membership),
    db: Session = Depends(get_db),
    service: CabinetService = Depends(get_cabinet_service),
) -> CompartmentDetailResponse:
    try:
        return service.get_compartment_detail(
            db, membership, cabinet_id, position
        )
    except AppException as exc:
        _raise_http_from_app_error(exc)


@router.get(
    "/{cabinet_id}/compartments/{position}/reveal",
    response_model=CompartmentRevealResponse,
    status_code=status.HTTP_200_OK,
)
def get_compartment_reveal(
    cabinet_id: int,
    position: int,
    membership: FamilyMembership = Depends(get_family_membership),
    db: Session = Depends(get_db),
    service: CabinetService = Depends(get_cabinet_service),
) -> CompartmentRevealResponse:
    try:
        return service.get_compartment_reveal(
            db, membership, cabinet_id, position
        )
    except AppException as exc:
        _raise_http_from_app_error(exc)


@router.put(
    "/{cabinet_id}/compartments/{position}/medication",
    response_model=CompartmentResponse,
    status_code=status.HTTP_200_OK,
)
def assign_medication_to_compartment(
    cabinet_id: int,
    position: int,
    payload: MedicationAssignmentRequest,
    membership: FamilyMembership = Depends(
        require_family_roles(*WRITE_CABINET_ROLES)
    ),
    db: Session = Depends(get_db),
    service: CabinetService = Depends(get_cabinet_service),
) -> CompartmentResponse:
    try:
        return service.assign_medication(
            db, membership, cabinet_id, position, payload
        )
    except AppException as exc:
        _raise_http_from_app_error(exc)


@router.delete(
    "/{cabinet_id}/compartments/{position}/medication",
    response_model=CompartmentResponse,
    status_code=status.HTTP_200_OK,
)
def unassign_medication_from_compartment(
    cabinet_id: int,
    position: int,
    membership: FamilyMembership = Depends(
        require_family_roles(*WRITE_CABINET_ROLES)
    ),
    db: Session = Depends(get_db),
    service: CabinetService = Depends(get_cabinet_service),
) -> CompartmentResponse:
    try:
        return service.unassign_medication(
            db, membership, cabinet_id, position
        )
    except AppException as exc:
        _raise_http_from_app_error(exc)


@router.post(
    "/{cabinet_id}/compartments/{position}/open",
    response_model=CompartmentResponse,
    status_code=status.HTTP_200_OK,
)
async def open_compartment(
    cabinet_id: int,
    position: int,
    membership: FamilyMembership = Depends(
        require_family_roles(*WRITE_CABINET_ROLES)
    ),
    db: Session = Depends(get_db),
    service: CabinetService = Depends(get_cabinet_service),
) -> CompartmentResponse:
    try:
        return await service.open_compartment(
            db, membership, cabinet_id, position
        )
    except AppException as exc:
        _raise_http_from_app_error(exc)


@router.post(
    "/{cabinet_id}/compartments/{position}/close",
    response_model=CompartmentResponse,
    status_code=status.HTTP_200_OK,
)
async def close_compartment(
    cabinet_id: int,
    position: int,
    membership: FamilyMembership = Depends(
        require_family_roles(*WRITE_CABINET_ROLES)
    ),
    db: Session = Depends(get_db),
    service: CabinetService = Depends(get_cabinet_service),
) -> CompartmentResponse:
    try:
        return await service.close_compartment(
            db, membership, cabinet_id, position
        )
    except AppException as exc:
        _raise_http_from_app_error(exc)


# ------------------------------------------------------------------
# Simulator & Event Endpoints
# ------------------------------------------------------------------


@router.post(
    "/{cabinet_id}/simulator/online",
    response_model=CabinetResponse,
    status_code=status.HTTP_200_OK,
)
async def set_simulator_online(
    cabinet_id: int,
    membership: FamilyMembership = Depends(
        require_family_roles(*WRITE_CABINET_ROLES)
    ),
    db: Session = Depends(get_db),
    service: CabinetService = Depends(get_cabinet_service),
) -> CabinetResponse:
    try:
        return await service.set_simulator_online(db, membership, cabinet_id)
    except AppException as exc:
        _raise_http_from_app_error(exc)


@router.post(
    "/{cabinet_id}/simulator/offline",
    response_model=CabinetResponse,
    status_code=status.HTTP_200_OK,
)
async def set_simulator_offline(
    cabinet_id: int,
    membership: FamilyMembership = Depends(
        require_family_roles(*WRITE_CABINET_ROLES)
    ),
    db: Session = Depends(get_db),
    service: CabinetService = Depends(get_cabinet_service),
) -> CabinetResponse:
    try:
        return await service.set_simulator_offline(db, membership, cabinet_id)
    except AppException as exc:
        _raise_http_from_app_error(exc)


@router.post(
    "/{cabinet_id}/simulator/sync",
    response_model=CabinetStateResponse,
    status_code=status.HTTP_200_OK,
)
async def sync_simulator_state(
    cabinet_id: int,
    membership: FamilyMembership = Depends(
        require_family_roles(*WRITE_CABINET_ROLES)
    ),
    db: Session = Depends(get_db),
    service: CabinetService = Depends(get_cabinet_service),
) -> CabinetStateResponse:
    try:
        return await service.sync_cabinet_state(db, membership, cabinet_id)
    except AppException as exc:
        _raise_http_from_app_error(exc)


@router.get(
    "/{cabinet_id}/events",
    response_model=CabinetEventListResponse,
    status_code=status.HTTP_200_OK,
)
def list_cabinet_events(
    cabinet_id: int,
    event_type: CabinetEventType | None = Query(default=None),
    from_time: datetime | None = Query(default=None, alias="from"),
    to_time: datetime | None = Query(default=None, alias="to"),
    limit: int = Query(default=100, ge=1, le=500),
    membership: FamilyMembership = Depends(get_family_membership),
    db: Session = Depends(get_db),
    service: CabinetService = Depends(get_cabinet_service),
) -> CabinetEventListResponse:
    try:
        return service.list_events(
            db,
            membership,
            cabinet_id,
            event_type=event_type,
            from_time=from_time,
            to_time=to_time,
            limit=limit,
        )
    except AppException as exc:
        _raise_http_from_app_error(exc)


# ------------------------------------------------------------------
# Realtime WebSocket Endpoint (§44, §45)
# ------------------------------------------------------------------


def _extract_ws_token(websocket: WebSocket) -> str | None:
    query_token = websocket.query_params.get("token")
    if query_token:
        return query_token.strip()
    auth_header = websocket.headers.get("authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        return auth_header[7:].strip()
    return None


@ws_router.websocket("/ws/families/{family_id}/cabinets/{cabinet_id}")
async def cabinet_websocket_endpoint(
    websocket: WebSocket,
    family_id: int,
    cabinet_id: int,
    db: Session = Depends(get_db),
) -> None:
    token = _extract_ws_token(websocket)
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        user_id = int(payload["sub"])
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    user_repo = UserRepository()
    user = user_repo.get_by_id(db, user_id)
    if user is None or user.status != "ACTIVE":
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    family_repo = FamilyRepository()
    membership = family_repo.get_membership(
        db,
        family_id=family_id,
        user_id=user.id,
    )
    if membership is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    cabinet_repo = CabinetRepository()
    cabinet = cabinet_repo.get_cabinet(
        db,
        family_id=family_id,
        cabinet_id=cabinet_id,
    )
    if cabinet is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket_manager.connect(family_id, cabinet_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        websocket_manager.disconnect(family_id, cabinet_id, websocket)
