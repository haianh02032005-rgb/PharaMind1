from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field

from backend.app.models.import_entity_link import ImportEntityLink
from backend.app.models.import_item import ImportItem
from backend.app.models.import_session import ImportSession
from backend.app.models.import_validation_issue import ImportValidationIssue
from backend.app.modules.imports.enums import (
    ImportMode,
    ImportResolutionStatus,
    ImportSourceType,
    ImportStatus,
    ValidationSeverity,
)


class ValidationIssueResponse(BaseModel):
    id: int
    import_session_id: int
    import_item_id: int | None = None
    severity: str
    code: str
    field_path: str
    message: str
    suggested_fix: str | None = None
    is_resolved: bool = False
    resolved_by_user_id: int | None = None
    resolved_at: datetime | None = None

    @classmethod
    def from_model(cls, model: ImportValidationIssue) -> "ValidationIssueResponse":
        return cls(
            id=model.id,
            import_session_id=model.import_session_id,
            import_item_id=model.import_item_id,
            severity=model.severity,
            code=model.code,
            field_path=model.field_path,
            message=model.message,
            suggested_fix=model.suggested_fix,
            is_resolved=model.is_resolved,
            resolved_by_user_id=model.resolved_by_user_id,
            resolved_at=model.resolved_at,
        )


class ImportItemResponse(BaseModel):
    id: int
    import_session_id: int
    row_index: int
    item_type: str
    raw_data: dict[str, Any] | None = None
    normalized_data: dict[str, Any] | None = None
    edited_data: dict[str, Any] | None = None
    confidence: float | None = None
    resolution_status: str
    matched_entity_type: str | None = None
    matched_entity_id: int | None = None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, model: ImportItem) -> "ImportItemResponse":
        return cls(
            id=model.id,
            import_session_id=model.import_session_id,
            row_index=model.row_index,
            item_type=model.item_type,
            raw_data=model.raw_data,
            normalized_data=model.normalized_data,
            edited_data=model.edited_data,
            confidence=model.confidence,
            resolution_status=model.resolution_status,
            matched_entity_type=model.matched_entity_type,
            matched_entity_id=model.matched_entity_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


class ImportEntityLinkResponse(BaseModel):
    id: int
    import_session_id: int
    entity_type: str
    entity_id: int
    action: str
    previous_snapshot: dict[str, Any] | None = None
    new_snapshot: dict[str, Any] | None = None
    created_at: datetime

    @classmethod
    def from_model(cls, model: ImportEntityLink) -> "ImportEntityLinkResponse":
        return cls(
            id=model.id,
            import_session_id=model.import_session_id,
            entity_type=model.entity_type,
            entity_id=model.entity_id,
            action=model.action,
            previous_snapshot=model.previous_snapshot,
            new_snapshot=model.new_snapshot,
            created_at=model.created_at,
        )


class ImportSessionResponse(BaseModel):
    id: int
    family_id: int
    member_id: int
    source_type: str
    source_filename: str
    source_hash: str
    mime_type: str | None = None
    file_size_bytes: int | None = None
    status: str
    import_mode: str
    overall_confidence: float | None = None
    parser_version: str
    raw_payload: dict[str, Any] | None = None
    normalized_payload: dict[str, Any] | None = None
    review_payload: dict[str, Any] | None = None
    commit_summary: dict[str, Any] | None = None
    target_prescription_id: int | None = None
    is_duplicate: bool = False
    duplicate_of_import_id: int | None = None
    created_by_user_id: int
    reviewed_by_user_id: int | None = None
    committed_by_user_id: int | None = None
    created_at: datetime
    updated_at: datetime
    committed_at: datetime | None = None
    items: list[ImportItemResponse] = Field(default_factory=list)
    validation_issues: list[ValidationIssueResponse] = Field(default_factory=list)
    entity_links: list[ImportEntityLinkResponse] = Field(default_factory=list)

    @classmethod
    def from_model(cls, model: ImportSession) -> "ImportSessionResponse":
        return cls(
            id=model.id,
            family_id=model.family_id,
            member_id=model.member_id,
            source_type=model.source_type,
            source_filename=model.source_filename,
            source_hash=model.source_hash,
            mime_type=model.mime_type,
            file_size_bytes=model.file_size_bytes,
            status=model.status,
            import_mode=model.import_mode,
            overall_confidence=model.overall_confidence,
            parser_version=model.parser_version,
            raw_payload=model.raw_payload,
            normalized_payload=model.normalized_payload,
            review_payload=model.review_payload,
            commit_summary=model.commit_summary,
            target_prescription_id=model.target_prescription_id,
            is_duplicate=model.is_duplicate,
            duplicate_of_import_id=model.duplicate_of_import_id,
            created_by_user_id=model.created_by_user_id,
            reviewed_by_user_id=model.reviewed_by_user_id,
            committed_by_user_id=model.committed_by_user_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            committed_at=model.committed_at,
            items=[ImportItemResponse.from_model(it) for it in model.items],
            validation_issues=[
                ValidationIssueResponse.from_model(iss)
                for iss in model.validation_issues
            ],
            entity_links=[
                ImportEntityLinkResponse.from_model(lnk)
                for lnk in model.entity_links
            ],
        )


class ImportSessionListResponse(BaseModel):
    items: list[ImportSessionResponse]


# ---------------------------------------------------------------------------
# Draft Update Schemas (§28.4)
# ---------------------------------------------------------------------------


class PrescriptionDraftUpdate(BaseModel):
    title: str | None = None
    doctor_name: str | None = None
    facility_name: str | None = None
    issued_at: date | str | None = None
    start_date: date | str | None = None
    end_date: date | str | None = None
    notes: str | None = None


class MedicationDraftItemUpdate(BaseModel):
    row_index: int
    action: str | None = None  # LINK_EXISTING | CREATE_NEW | UPDATE_ITEM | SKIP
    family_medication_id: int | None = None
    catalog_id: int | None = None
    medication_name: str | None = None
    active_ingredient: str | None = None
    strength: str | None = None
    dosage_form: str | None = None
    dose_amount: float | None = None
    dose_unit: str | None = None
    frequency_per_day: float | None = None
    frequency_text: str | None = None
    route: str | None = None
    instructions: str | None = None
    quantity: float | None = None
    unit: str | None = None
    expiration_date: date | str | None = None
    create_schedule: bool | None = None
    schedule_times: list[str] | None = None
    recurrence_type: str | None = None
    reminder_enabled: bool | None = None
    reminder_before_minutes: int | None = None
    grace_period_minutes: int | None = None
    start_date: date | str | None = None
    end_date: date | str | None = None


class HealthConditionDraftItem(BaseModel):
    name: str
    diagnosed_at: date | str | None = None
    status: str = "ACTIVE"
    notes: str | None = None
    confirmed: bool = True


class AllergyDraftItem(BaseModel):
    allergen: str
    allergy_type: str = "DRUG"
    severity: str = "UNKNOWN"
    reaction_description: str | None = None
    notes: str | None = None
    confirmed: bool = True


class DrugReactionDraftItem(BaseModel):
    drug_name: str
    active_ingredient: str | None = None
    reaction: str
    severity: str = "UNKNOWN"
    occurred_at: date | str | None = None
    notes: str | None = None
    confirmed: bool = True


class HealthUpdatesDraft(BaseModel):
    confirm_conditions: bool = False
    conditions: list[HealthConditionDraftItem] | None = None
    confirm_allergies: bool = False
    allergies: list[AllergyDraftItem] | None = None
    confirm_drug_reactions: bool = False
    drug_reactions: list[DrugReactionDraftItem] | None = None
    general_notes_append: str | None = None


class ImportDraftUpdateRequest(BaseModel):
    import_mode: ImportMode | None = None
    target_prescription_id: int | None = None
    confirm_member_match: bool | None = None
    confirm_duplicate_override: bool | None = None
    prescription: PrescriptionDraftUpdate | None = None
    items: list[MedicationDraftItemUpdate] | None = None
    health_updates: HealthUpdatesDraft | None = None
    resolved_issue_ids: list[int] | None = None


class ImportCommitRequest(BaseModel):
    confirm_member_id: int
    confirm_import_mode: ImportMode = ImportMode.CREATE_NEW_PRESCRIPTION
    confirm_schedule_creation: bool = True
    confirm_health_updates: bool = False
    simulate_failure: bool = False  # For testing transaction rollback (§32.9)


class ImportRejectRequest(BaseModel):
    reason: str | None = None

