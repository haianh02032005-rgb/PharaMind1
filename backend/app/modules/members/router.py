from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from backend.app.api.dependencies import get_db
from backend.app.core.exceptions import AppException
from backend.app.models.family_membership import FamilyMembership
from backend.app.modules.families.dependencies import (
    get_family_membership,
    require_family_roles,
)
from backend.app.modules.medications.schema import MedicationListResponse
from backend.app.modules.medications.service import MedicationService
from backend.app.modules.prescriptions.schema import PrescriptionListResponse
from backend.app.modules.prescriptions.service import PrescriptionService
from backend.app.modules.schedules.enums import ScheduleStatus
from backend.app.modules.schedules.schema import (
    DailyScheduleResponse,
    MedicationScheduleListResponse,
    NextDoseResponse,
)
from backend.app.modules.schedules.service import ScheduleService
from backend.app.modules.members.schema import (
    AllergyCreateRequest,
    AllergyListResponse,
    AllergyResponse,
    AllergyUpdateRequest,
    DrugReactionCreateRequest,
    DrugReactionListResponse,
    DrugReactionResponse,
    DrugReactionUpdateRequest,
    EmergencyContactCreateRequest,
    EmergencyContactListResponse,
    EmergencyContactResponse,
    EmergencyContactUpdateRequest,
    HealthProfileResponse,
    HealthProfileUpdateRequest,
    MedicalConditionCreateRequest,
    MedicalConditionListResponse,
    MedicalConditionResponse,
    MedicalConditionUpdateRequest,
    MemberCreateRequest,
    MemberListResponse,
    MemberResponse,
    MemberUpdateRequest,
)
from backend.app.modules.members.service import MemberService
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


def get_member_service() -> MemberService:
    return MemberService()


def get_medication_service() -> MedicationService:
    return MedicationService()


def get_prescription_service() -> PrescriptionService:
    return PrescriptionService()


def get_schedule_service() -> ScheduleService:
    return ScheduleService()


def _raise_http_from_app_error(exc: AppException) -> None:
    raise HTTPException(
        status_code=exc.status_code,
        detail=exc.detail,
    ) from exc


# ------------------------------------------------------------------
# FamilyMember Endpoints
# ------------------------------------------------------------------


@router.post(
    "",
    response_model=MemberResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_member(
    payload: MemberCreateRequest,
    membership: FamilyMembership = Depends(require_family_roles(*WRITE_ROLES)),
    db: Session = Depends(get_db),
    service: MemberService = Depends(get_member_service),
) -> MemberResponse:
    try:
        return service.create_member(db, membership, payload)
    except AppException as exc:
        _raise_http_from_app_error(exc)


@router.get(
    "",
    response_model=MemberListResponse,
    status_code=status.HTTP_200_OK,
)
def list_members(
    include_archived: bool = Query(default=False),
    membership: FamilyMembership = Depends(get_family_membership),
    db: Session = Depends(get_db),
    service: MemberService = Depends(get_member_service),
) -> MemberListResponse:
    try:
        return service.list_members(
            db,
            membership,
            include_archived=include_archived,
        )
    except AppException as exc:
        _raise_http_from_app_error(exc)


@router.get(
    "/{member_id}",
    response_model=MemberResponse,
    status_code=status.HTTP_200_OK,
)
def get_member(
    member_id: int,
    membership: FamilyMembership = Depends(get_family_membership),
    db: Session = Depends(get_db),
    service: MemberService = Depends(get_member_service),
) -> MemberResponse:
    try:
        return service.get_member_detail(db, membership, member_id)
    except AppException as exc:
        _raise_http_from_app_error(exc)


@router.patch(
    "/{member_id}",
    response_model=MemberResponse,
    status_code=status.HTTP_200_OK,
)
def update_member(
    member_id: int,
    payload: MemberUpdateRequest,
    membership: FamilyMembership = Depends(require_family_roles(*WRITE_ROLES)),
    db: Session = Depends(get_db),
    service: MemberService = Depends(get_member_service),
) -> MemberResponse:
    try:
        return service.update_member(db, membership, member_id, payload)
    except AppException as exc:
        _raise_http_from_app_error(exc)


@router.post(
    "/{member_id}/archive",
    response_model=MemberResponse,
    status_code=status.HTTP_200_OK,
)
def archive_member(
    member_id: int,
    membership: FamilyMembership = Depends(require_family_roles(*ADMIN_ROLES)),
    db: Session = Depends(get_db),
    service: MemberService = Depends(get_member_service),
) -> MemberResponse:
    try:
        return service.archive_member(db, membership, member_id)
    except AppException as exc:
        _raise_http_from_app_error(exc)


@router.post(
    "/{member_id}/restore",
    response_model=MemberResponse,
    status_code=status.HTTP_200_OK,
)
def restore_member(
    member_id: int,
    membership: FamilyMembership = Depends(require_family_roles(*ADMIN_ROLES)),
    db: Session = Depends(get_db),
    service: MemberService = Depends(get_member_service),
) -> MemberResponse:
    try:
        return service.restore_member(db, membership, member_id)
    except AppException as exc:
        _raise_http_from_app_error(exc)


# ------------------------------------------------------------------
# HealthProfile Endpoints
# ------------------------------------------------------------------


@router.get(
    "/{member_id}/health-profile",
    response_model=HealthProfileResponse,
    status_code=status.HTTP_200_OK,
)
def get_health_profile(
    member_id: int,
    membership: FamilyMembership = Depends(get_family_membership),
    db: Session = Depends(get_db),
    service: MemberService = Depends(get_member_service),
) -> HealthProfileResponse:
    try:
        return service.get_health_profile(db, membership, member_id)
    except AppException as exc:
        _raise_http_from_app_error(exc)


@router.patch(
    "/{member_id}/health-profile",
    response_model=HealthProfileResponse,
    status_code=status.HTTP_200_OK,
)
def update_health_profile(
    member_id: int,
    payload: HealthProfileUpdateRequest,
    membership: FamilyMembership = Depends(require_family_roles(*WRITE_ROLES)),
    db: Session = Depends(get_db),
    service: MemberService = Depends(get_member_service),
) -> HealthProfileResponse:
    try:
        return service.update_health_profile(db, membership, member_id, payload)
    except AppException as exc:
        _raise_http_from_app_error(exc)


# ------------------------------------------------------------------
# MedicalCondition Endpoints
# ------------------------------------------------------------------


@router.get(
    "/{member_id}/conditions",
    response_model=MedicalConditionListResponse,
    status_code=status.HTTP_200_OK,
)
def list_conditions(
    member_id: int,
    membership: FamilyMembership = Depends(get_family_membership),
    db: Session = Depends(get_db),
    service: MemberService = Depends(get_member_service),
) -> MedicalConditionListResponse:
    try:
        return service.list_conditions(db, membership, member_id)
    except AppException as exc:
        _raise_http_from_app_error(exc)


@router.post(
    "/{member_id}/conditions",
    response_model=MedicalConditionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_condition(
    member_id: int,
    payload: MedicalConditionCreateRequest,
    membership: FamilyMembership = Depends(require_family_roles(*WRITE_ROLES)),
    db: Session = Depends(get_db),
    service: MemberService = Depends(get_member_service),
) -> MedicalConditionResponse:
    try:
        return service.create_condition(db, membership, member_id, payload)
    except AppException as exc:
        _raise_http_from_app_error(exc)


@router.patch(
    "/{member_id}/conditions/{condition_id}",
    response_model=MedicalConditionResponse,
    status_code=status.HTTP_200_OK,
)
def update_condition(
    member_id: int,
    condition_id: int,
    payload: MedicalConditionUpdateRequest,
    membership: FamilyMembership = Depends(require_family_roles(*WRITE_ROLES)),
    db: Session = Depends(get_db),
    service: MemberService = Depends(get_member_service),
) -> MedicalConditionResponse:
    try:
        return service.update_condition(
            db, membership, member_id, condition_id, payload
        )
    except AppException as exc:
        _raise_http_from_app_error(exc)


@router.delete(
    "/{member_id}/conditions/{condition_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_condition(
    member_id: int,
    condition_id: int,
    membership: FamilyMembership = Depends(require_family_roles(*WRITE_ROLES)),
    db: Session = Depends(get_db),
    service: MemberService = Depends(get_member_service),
) -> Response:
    try:
        service.delete_condition(db, membership, member_id, condition_id)
    except AppException as exc:
        _raise_http_from_app_error(exc)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ------------------------------------------------------------------
# AllergyProfile Endpoints
# ------------------------------------------------------------------


@router.get(
    "/{member_id}/allergies",
    response_model=AllergyListResponse,
    status_code=status.HTTP_200_OK,
)
def list_allergies(
    member_id: int,
    membership: FamilyMembership = Depends(get_family_membership),
    db: Session = Depends(get_db),
    service: MemberService = Depends(get_member_service),
) -> AllergyListResponse:
    try:
        return service.list_allergies(db, membership, member_id)
    except AppException as exc:
        _raise_http_from_app_error(exc)


@router.post(
    "/{member_id}/allergies",
    response_model=AllergyResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_allergy(
    member_id: int,
    payload: AllergyCreateRequest,
    membership: FamilyMembership = Depends(require_family_roles(*WRITE_ROLES)),
    db: Session = Depends(get_db),
    service: MemberService = Depends(get_member_service),
) -> AllergyResponse:
    try:
        return service.create_allergy(db, membership, member_id, payload)
    except AppException as exc:
        _raise_http_from_app_error(exc)


@router.patch(
    "/{member_id}/allergies/{allergy_id}",
    response_model=AllergyResponse,
    status_code=status.HTTP_200_OK,
)
def update_allergy(
    member_id: int,
    allergy_id: int,
    payload: AllergyUpdateRequest,
    membership: FamilyMembership = Depends(require_family_roles(*WRITE_ROLES)),
    db: Session = Depends(get_db),
    service: MemberService = Depends(get_member_service),
) -> AllergyResponse:
    try:
        return service.update_allergy(
            db, membership, member_id, allergy_id, payload
        )
    except AppException as exc:
        _raise_http_from_app_error(exc)


@router.delete(
    "/{member_id}/allergies/{allergy_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_allergy(
    member_id: int,
    allergy_id: int,
    membership: FamilyMembership = Depends(require_family_roles(*WRITE_ROLES)),
    db: Session = Depends(get_db),
    service: MemberService = Depends(get_member_service),
) -> Response:
    try:
        service.delete_allergy(db, membership, member_id, allergy_id)
    except AppException as exc:
        _raise_http_from_app_error(exc)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ------------------------------------------------------------------
# DrugReactionHistory Endpoints
# ------------------------------------------------------------------


@router.get(
    "/{member_id}/drug-reactions",
    response_model=DrugReactionListResponse,
    status_code=status.HTTP_200_OK,
)
def list_drug_reactions(
    member_id: int,
    membership: FamilyMembership = Depends(get_family_membership),
    db: Session = Depends(get_db),
    service: MemberService = Depends(get_member_service),
) -> DrugReactionListResponse:
    try:
        return service.list_drug_reactions(db, membership, member_id)
    except AppException as exc:
        _raise_http_from_app_error(exc)


@router.post(
    "/{member_id}/drug-reactions",
    response_model=DrugReactionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_drug_reaction(
    member_id: int,
    payload: DrugReactionCreateRequest,
    membership: FamilyMembership = Depends(require_family_roles(*WRITE_ROLES)),
    db: Session = Depends(get_db),
    service: MemberService = Depends(get_member_service),
) -> DrugReactionResponse:
    try:
        return service.create_drug_reaction(db, membership, member_id, payload)
    except AppException as exc:
        _raise_http_from_app_error(exc)


@router.patch(
    "/{member_id}/drug-reactions/{reaction_id}",
    response_model=DrugReactionResponse,
    status_code=status.HTTP_200_OK,
)
def update_drug_reaction(
    member_id: int,
    reaction_id: int,
    payload: DrugReactionUpdateRequest,
    membership: FamilyMembership = Depends(require_family_roles(*WRITE_ROLES)),
    db: Session = Depends(get_db),
    service: MemberService = Depends(get_member_service),
) -> DrugReactionResponse:
    try:
        return service.update_drug_reaction(
            db, membership, member_id, reaction_id, payload
        )
    except AppException as exc:
        _raise_http_from_app_error(exc)


@router.delete(
    "/{member_id}/drug-reactions/{reaction_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_drug_reaction(
    member_id: int,
    reaction_id: int,
    membership: FamilyMembership = Depends(require_family_roles(*WRITE_ROLES)),
    db: Session = Depends(get_db),
    service: MemberService = Depends(get_member_service),
) -> Response:
    try:
        service.delete_drug_reaction(db, membership, member_id, reaction_id)
    except AppException as exc:
        _raise_http_from_app_error(exc)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ------------------------------------------------------------------
# EmergencyContact Endpoints
# ------------------------------------------------------------------


@router.get(
    "/{member_id}/emergency-contacts",
    response_model=EmergencyContactListResponse,
    status_code=status.HTTP_200_OK,
)
def list_emergency_contacts(
    member_id: int,
    membership: FamilyMembership = Depends(get_family_membership),
    db: Session = Depends(get_db),
    service: MemberService = Depends(get_member_service),
) -> EmergencyContactListResponse:
    try:
        return service.list_emergency_contacts(db, membership, member_id)
    except AppException as exc:
        _raise_http_from_app_error(exc)


@router.post(
    "/{member_id}/emergency-contacts",
    response_model=EmergencyContactResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_emergency_contact(
    member_id: int,
    payload: EmergencyContactCreateRequest,
    membership: FamilyMembership = Depends(require_family_roles(*WRITE_ROLES)),
    db: Session = Depends(get_db),
    service: MemberService = Depends(get_member_service),
) -> EmergencyContactResponse:
    try:
        return service.create_emergency_contact(
            db, membership, member_id, payload
        )
    except AppException as exc:
        _raise_http_from_app_error(exc)


@router.patch(
    "/{member_id}/emergency-contacts/{contact_id}",
    response_model=EmergencyContactResponse,
    status_code=status.HTTP_200_OK,
)
def update_emergency_contact(
    member_id: int,
    contact_id: int,
    payload: EmergencyContactUpdateRequest,
    membership: FamilyMembership = Depends(require_family_roles(*WRITE_ROLES)),
    db: Session = Depends(get_db),
    service: MemberService = Depends(get_member_service),
) -> EmergencyContactResponse:
    try:
        return service.update_emergency_contact(
            db, membership, member_id, contact_id, payload
        )
    except AppException as exc:
        _raise_http_from_app_error(exc)


@router.delete(
    "/{member_id}/emergency-contacts/{contact_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_emergency_contact(
    member_id: int,
    contact_id: int,
    membership: FamilyMembership = Depends(require_family_roles(*WRITE_ROLES)),
    db: Session = Depends(get_db),
    service: MemberService = Depends(get_member_service),
) -> Response:
    try:
        service.delete_emergency_contact(db, membership, member_id, contact_id)
    except AppException as exc:
        _raise_http_from_app_error(exc)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ------------------------------------------------------------------
# Member Medications Endpoint (TASK 06 §46)
# ------------------------------------------------------------------


@router.get(
    "/{member_id}/medications",
    response_model=MedicationListResponse,
    status_code=status.HTTP_200_OK,
)
def list_member_medications(
    member_id: int,
    include_archived: bool = Query(default=False),
    membership: FamilyMembership = Depends(get_family_membership),
    db: Session = Depends(get_db),
    service: MedicationService = Depends(get_medication_service),
) -> MedicationListResponse:
    try:
        return service.list_member_medications(
            db,
            membership,
            member_id,
            include_archived=include_archived,
        )
    except AppException as exc:
        _raise_http_from_app_error(exc)


@router.get(
    "/{member_id}/prescriptions",
    response_model=PrescriptionListResponse,
    status_code=status.HTTP_200_OK,
)
def list_member_prescriptions(
    member_id: int,
    include_archived: bool = Query(default=False),
    membership: FamilyMembership = Depends(get_family_membership),
    db: Session = Depends(get_db),
    service: PrescriptionService = Depends(get_prescription_service),
) -> PrescriptionListResponse:
    try:
        return service.list_member_prescriptions(
            db,
            membership,
            member_id,
            include_archived=include_archived,
        )
    except AppException as exc:
        _raise_http_from_app_error(exc)


# ------------------------------------------------------------------
# Member Schedule Endpoints (TASK 08 §23, §32, §34)
# ------------------------------------------------------------------


@router.get(
    "/{member_id}/schedules",
    response_model=MedicationScheduleListResponse,
    status_code=status.HTTP_200_OK,
)
def list_member_schedules(
    member_id: int,
    status_filter: ScheduleStatus | None = Query(default=None, alias="status"),
    include_archived: bool = Query(default=False),
    membership: FamilyMembership = Depends(get_family_membership),
    db: Session = Depends(get_db),
    service: ScheduleService = Depends(get_schedule_service),
) -> MedicationScheduleListResponse:
    try:
        return service.list_member_schedules(
            db,
            membership,
            member_id,
            status=status_filter,
            include_archived=include_archived,
        )
    except AppException as exc:
        _raise_http_from_app_error(exc)


@router.get(
    "/{member_id}/schedule-day",
    response_model=DailyScheduleResponse,
    status_code=status.HTTP_200_OK,
)
def get_member_daily_schedule(
    member_id: int,
    target_date: date | None = Query(default=None, alias="date"),
    membership: FamilyMembership = Depends(get_family_membership),
    db: Session = Depends(get_db),
    service: ScheduleService = Depends(get_schedule_service),
) -> DailyScheduleResponse:
    try:
        return service.get_daily_schedule(
            db,
            membership,
            member_id,
            target_date=target_date,
        )
    except AppException as exc:
        _raise_http_from_app_error(exc)


@router.get(
    "/{member_id}/next-dose",
    response_model=NextDoseResponse,
    status_code=status.HTTP_200_OK,
)
def get_member_next_dose(
    member_id: int,
    now: datetime | None = Query(default=None),
    membership: FamilyMembership = Depends(get_family_membership),
    db: Session = Depends(get_db),
    service: ScheduleService = Depends(get_schedule_service),
) -> NextDoseResponse:
    try:
        return service.get_next_dose(
            db,
            membership,
            member_id,
            now=now,
        )
    except AppException as exc:
        _raise_http_from_app_error(exc)



