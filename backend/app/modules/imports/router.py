from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status
from sqlalchemy.orm import Session

from backend.app.api.dependencies import get_db
from backend.app.core.exceptions import AppException
from backend.app.models.family_membership import FamilyMembership
from backend.app.models.user import User
from backend.app.modules.auth.dependencies import get_current_user
from backend.app.modules.families.dependencies import get_family_membership
from backend.app.modules.imports.schema import (
    ImportCommitRequest,
    ImportDraftUpdateRequest,
    ImportRejectRequest,
    ImportSessionListResponse,
    ImportSessionResponse,
)
from backend.app.modules.imports.service import ImportService

router = APIRouter()
template_router = APIRouter()


def get_import_service() -> ImportService:
    return ImportService()


def _raise_http(exc: AppException) -> None:
    raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.post(
    "",
    response_model=ImportSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload OCR image/PDF or Excel/CSV file to create a staging import session",
)
def create_import_session(
    member_id: int,
    file: UploadFile = File(...),
    source_type: str | None = Form(default=None),
    import_mode: str | None = Form(default="CREATE_NEW_PRESCRIPTION"),
    target_prescription_id: int | None = Form(default=None),
    membership: FamilyMembership = Depends(get_family_membership),
    db: Session = Depends(get_db),
    service: ImportService = Depends(get_import_service),
) -> ImportSessionResponse:
    file_ext = (file.filename or "").rsplit(".", 1)[-1].lower()
    max_bytes = 20 * 1024 * 1024 if file_ext == "pdf" else 10 * 1024 * 1024
    file_bytes = file.file.read(max_bytes + 1)
    if len(file_bytes) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Tệp vượt quá giới hạn {max_bytes // (1024 * 1024)}MB.",
        )
    try:
        return service.upload_and_parse(
            db,
            membership=membership,
            member_id=member_id,
            filename=file.filename or "upload.xlsx",
            content_type=file.content_type,
            file_bytes=file_bytes,
            source_type=source_type,
            import_mode=import_mode,
            target_prescription_id=target_prescription_id,
        )
    except AppException as exc:
        _raise_http(exc)


@router.get("", response_model=ImportSessionListResponse)
def list_import_sessions(
    member_id: int,
    membership: FamilyMembership = Depends(get_family_membership),
    db: Session = Depends(get_db),
    service: ImportService = Depends(get_import_service),
) -> ImportSessionListResponse:
    try:
        return service.list_sessions(db, membership=membership, member_id=member_id)
    except AppException as exc:
        _raise_http(exc)


@router.get("/{import_id}", response_model=ImportSessionResponse)
def get_import_session(
    member_id: int,
    import_id: int,
    membership: FamilyMembership = Depends(get_family_membership),
    db: Session = Depends(get_db),
    service: ImportService = Depends(get_import_service),
) -> ImportSessionResponse:
    try:
        return service.get_session(
            db, membership=membership, member_id=member_id, import_id=import_id
        )
    except AppException as exc:
        _raise_http(exc)


@router.patch("/{import_id}/draft", response_model=ImportSessionResponse)
def update_import_draft(
    member_id: int,
    import_id: int,
    payload: ImportDraftUpdateRequest,
    membership: FamilyMembership = Depends(get_family_membership),
    db: Session = Depends(get_db),
    service: ImportService = Depends(get_import_service),
) -> ImportSessionResponse:
    try:
        return service.update_draft(
            db,
            membership=membership,
            member_id=member_id,
            import_id=import_id,
            payload=payload,
        )
    except AppException as exc:
        _raise_http(exc)


@router.post("/{import_id}/validate", response_model=ImportSessionResponse)
def validate_import_session(
    member_id: int,
    import_id: int,
    membership: FamilyMembership = Depends(get_family_membership),
    db: Session = Depends(get_db),
    service: ImportService = Depends(get_import_service),
) -> ImportSessionResponse:
    try:
        return service.validate_session(
            db, membership=membership, member_id=member_id, import_id=import_id
        )
    except AppException as exc:
        _raise_http(exc)


@router.post("/{import_id}/commit", response_model=ImportSessionResponse)
def commit_import_session(
    member_id: int,
    import_id: int,
    payload: ImportCommitRequest,
    membership: FamilyMembership = Depends(get_family_membership),
    db: Session = Depends(get_db),
    service: ImportService = Depends(get_import_service),
) -> ImportSessionResponse:
    try:
        return service.commit_session(
            db,
            membership=membership,
            member_id=member_id,
            import_id=import_id,
            payload=payload,
        )
    except AppException as exc:
        _raise_http(exc)


@router.post("/{import_id}/reject", response_model=ImportSessionResponse)
def reject_import_session(
    member_id: int,
    import_id: int,
    payload: ImportRejectRequest | None = None,
    membership: FamilyMembership = Depends(get_family_membership),
    db: Session = Depends(get_db),
    service: ImportService = Depends(get_import_service),
) -> ImportSessionResponse:
    try:
        return service.reject_session(
            db,
            membership=membership,
            member_id=member_id,
            import_id=import_id,
            payload=payload,
        )
    except AppException as exc:
        _raise_http(exc)


@template_router.get(
    "/templates/prescription.xlsx",
    summary="Download PHARMAMIND_PRESCRIPTION_IMPORT_TEMPLATE.xlsx",
)
def download_prescription_excel_template(
    current_user: User = Depends(get_current_user),
) -> Response:
    return Response(
        content=ImportService.get_template_xlsx_bytes(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": 'attachment; filename="PHARMAMIND_PRESCRIPTION_IMPORT_TEMPLATE.xlsx"'
        },
    )
