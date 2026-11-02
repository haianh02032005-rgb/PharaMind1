import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.family import Family
from backend.app.models.family_member import FamilyMember
from backend.app.models.family_membership import FamilyMembership
from backend.app.models.import_item import ImportItem
from backend.app.models.import_session import ImportSession
from backend.app.models.import_validation_issue import ImportValidationIssue
from backend.app.models.prescription import Prescription
from backend.app.modules.families.exceptions import (
    FamilyArchivedError,
    InsufficientFamilyPermissionError,
)
from backend.app.modules.imports.adapters.excel_adapter import (
    ExcelImportAdapter,
    generate_template_xlsx,
)
from backend.app.modules.imports.adapters.ocr_adapter import OCRImportAdapter
from backend.app.modules.imports.commit.import_commit_service import (
    ImportCommitService,
)
from backend.app.modules.imports.enums import (
    ImportItemType,
    ImportMode,
    ImportResolutionStatus,
    ImportSourceType,
    ImportStatus,
    ValidationSeverity,
)
from backend.app.modules.imports.exceptions import (
    ImportAlreadyCommittedError,
    ImportSessionNotFoundError,
    ImportUnsupportedFileError,
    ImportValidationBlockedError,
)
from backend.app.modules.imports.normalizers.date_normalizer import (
    normalize_date,
    normalize_time_string,
)
from backend.app.modules.imports.normalizers.dosage_normalizer import (
    normalize_dosage_form,
    normalize_route,
    normalize_unit,
)
from backend.app.modules.imports.parsers.health_parser import (
    parse_health_candidates,
)
from backend.app.modules.imports.parsers.medication_parser import (
    parse_medication_item,
)
from backend.app.modules.imports.parsers.prescription_parser import (
    parse_prescription_meta,
)
from backend.app.modules.imports.parsers.schedule_parser import (
    parse_schedule_candidate,
)
from backend.app.modules.imports.repository import ImportRepository
from backend.app.modules.imports.resolvers.medication_resolver import (
    resolve_medication_item,
)
from backend.app.modules.imports.resolvers.member_resolver import (
    resolve_member_identity,
)
from backend.app.modules.imports.resolvers.prescription_resolver import (
    compute_prescription_diff,
)
from backend.app.modules.imports.schema import (
    ImportCommitRequest,
    ImportDraftUpdateRequest,
    ImportRejectRequest,
    ImportSessionListResponse,
    ImportSessionResponse,
)
from backend.app.modules.imports.validators.health_validator import (
    validate_health_candidates,
)
from backend.app.modules.imports.validators.medication_validator import (
    validate_medication_items,
)
from backend.app.modules.imports.validators.prescription_validator import (
    validate_prescription_header,
)
from backend.app.modules.imports.validators.schedule_validator import (
    validate_schedule_candidates,
)
from backend.app.modules.members.exceptions import MemberNotFoundError
from backend.app.modules.members.repository import MemberRepository
from backend.app.shared.enums import FamilyRole, FamilyStatus

WRITE_IMPORT_ROLES = (
    FamilyRole.OWNER,
    FamilyRole.ADMIN,
    FamilyRole.CAREGIVER,
)

ALLOWED_EXTENSIONS: dict[str, ImportSourceType] = {
    "jpg": ImportSourceType.OCR_IMAGE,
    "jpeg": ImportSourceType.OCR_IMAGE,
    "png": ImportSourceType.OCR_IMAGE,
    "pdf": ImportSourceType.OCR_PDF,
    "xlsx": ImportSourceType.EXCEL_XLSX,
    "csv": ImportSourceType.CSV,
}

MAX_PDF_BYTES = 20 * 1024 * 1024
MAX_OTHER_BYTES = 10 * 1024 * 1024

STORAGE_ROOT = Path("storage/imports")


class ImportService:
    def __init__(
        self,
        repository: ImportRepository | None = None,
        member_repository: MemberRepository | None = None,
        ocr_adapter: OCRImportAdapter | None = None,
        excel_adapter: ExcelImportAdapter | None = None,
        commit_service: ImportCommitService | None = None,
    ) -> None:
        self.repository = repository or ImportRepository()
        self.member_repository = member_repository or MemberRepository()
        self.ocr_adapter = ocr_adapter or OCRImportAdapter()
        self.excel_adapter = excel_adapter or ExcelImportAdapter()
        self.commit_service = commit_service or ImportCommitService()

    # ------------------------------------------------------------------
    # 1. Upload & Create Staging Session
    # ------------------------------------------------------------------

    def upload_and_parse(
        self,
        db: Session,
        *,
        membership: FamilyMembership,
        member_id: int,
        filename: str,
        content_type: str | None,
        file_bytes: bytes,
        source_type: str | None = None,
        import_mode: str | None = None,
        target_prescription_id: int | None = None,
    ) -> ImportSessionResponse:
        self._ensure_roles(membership, *WRITE_IMPORT_ROLES)
        self._ensure_family_active(membership.family)
        member = self._get_scoped_member(db, membership, member_id)

        resolved_source_type, ext = self._validate_file(
            filename=filename,
            file_bytes=file_bytes,
            explicit_source_type=source_type,
        )

        resolved_mode = (
            import_mode
            if import_mode in {m.value for m in ImportMode}
            else ImportMode.CREATE_NEW_PRESCRIPTION.value
        )

        # Compute SHA-256 hash & check duplicates (§17)
        source_hash = hashlib.sha256(file_bytes).hexdigest()
        existing_dup = self.repository.find_by_hash(
            db,
            family_id=membership.family_id,
            member_id=member.id,
            source_hash=source_hash,
        )
        is_duplicate = existing_dup is not None
        duplicate_of_id = existing_dup.id if existing_dup else None

        # Store private file (§25)
        storage_path = self._save_private_file(
            family_id=membership.family_id,
            member_id=member.id,
            ext=ext,
            file_bytes=file_bytes,
        )

        # Extract raw data via OCR or Excel adapter
        adapter = (
            self.excel_adapter
            if resolved_source_type
            in {ImportSourceType.EXCEL_XLSX.value, ImportSourceType.CSV.value}
            else self.ocr_adapter
        )
        raw_payload = adapter.extract(
            file_bytes,
            filename,
            default_member_name=member.full_name,
        )

        # Normalize & build staging payload
        raw_meta = raw_payload.get("prescription_meta") or {}
        raw_meds = raw_payload.get("medications") or []

        prescription_meta = parse_prescription_meta(raw_meta)
        member_resolution = resolve_member_identity(member, prescription_meta)

        normalized_items: list[dict[str, Any]] = []
        for idx, r_med in enumerate(raw_meds):
            norm_med = parse_medication_item(r_med, idx)
            sched_cand = parse_schedule_candidate(r_med, norm_med, prescription_meta)
            med_res = resolve_medication_item(
                db,
                family_id=membership.family_id,
                member_id=member.id,
                med_item=norm_med,
            )
            merged_item = {
                **norm_med,
                **med_res,
                "schedule": sched_cand,
                "user_edited": False,
            }
            normalized_items.append(merged_item)

        health_draft = parse_health_candidates(raw_meta, raw_meds)

        target_rx = self._get_target_prescription(
            db,
            family_id=membership.family_id,
            member_id=member.id,
            target_prescription_id=target_prescription_id,
        )
        prescription_diff = compute_prescription_diff(
            db,
            target_prescription=target_rx,
            prescription_draft=prescription_meta,
            med_items_draft=normalized_items,
        )

        normalized_payload = {
            "member_resolution": member_resolution,
            "prescription": prescription_meta,
            "items": normalized_items,
            "health_updates": health_draft,
            "prescription_diff": prescription_diff,
        }
        review_payload = dict(normalized_payload)

        session_obj = ImportSession(
            family_id=membership.family_id,
            member_id=member.id,
            source_type=resolved_source_type,
            source_filename=filename,
            source_hash=source_hash,
            storage_path=storage_path,
            mime_type=content_type,
            file_size_bytes=len(file_bytes),
            status=ImportStatus.REVIEW_REQUIRED.value,
            import_mode=resolved_mode,
            overall_confidence=float(raw_payload.get("overall_confidence", 1.0)),
            parser_version=adapter.parser_version,
            raw_payload=raw_payload,
            normalized_payload=normalized_payload,
            review_payload=review_payload,
            target_prescription_id=target_prescription_id,
            is_duplicate=is_duplicate,
            duplicate_of_import_id=duplicate_of_id,
            created_by_user_id=membership.user_id,
        )
        self.repository.create_session(db, session_obj)

        # Create ImportItem rows
        for idx, item_data in enumerate(normalized_items):
            raw_row = raw_meds[idx] if idx < len(raw_meds) else {}
            imp_item = ImportItem(
                import_session_id=session_obj.id,
                row_index=idx,
                item_type=ImportItemType.MEDICATION_ITEM.value,
                raw_data=raw_row,
                normalized_data=item_data,
                edited_data=item_data,
                confidence=item_data.get("confidence", 1.0),
                resolution_status=item_data.get(
                    "resolution_status", ImportResolutionStatus.CREATE_NEW.value
                ),
                matched_entity_type=item_data.get("matched_entity_type"),
                matched_entity_id=item_data.get("matched_entity_id"),
            )
            self.repository.add_item(db, imp_item)

        # Run initial validation and update status (REVIEW_REQUIRED vs READY_TO_COMMIT)
        self._rebuild_validation_issues(db, session_obj=session_obj, member=member)

        db.commit()
        db.refresh(session_obj)
        return ImportSessionResponse.from_model(session_obj)

    # ------------------------------------------------------------------
    # 2. List & Get Session
    # ------------------------------------------------------------------

    def list_sessions(
        self,
        db: Session,
        *,
        membership: FamilyMembership,
        member_id: int,
    ) -> ImportSessionListResponse:
        member = self._get_scoped_member(db, membership, member_id)
        rows = self.repository.list_sessions(
            db,
            family_id=membership.family_id,
            member_id=member.id,
        )
        return ImportSessionListResponse(
            items=[ImportSessionResponse.from_model(r) for r in rows]
        )

    def get_session(
        self,
        db: Session,
        *,
        membership: FamilyMembership,
        member_id: int,
        import_id: int,
    ) -> ImportSessionResponse:
        member = self._get_scoped_member(db, membership, member_id)
        session_obj = self._get_scoped_session(
            db,
            family_id=membership.family_id,
            member_id=member.id,
            import_id=import_id,
        )
        return ImportSessionResponse.from_model(session_obj)

    # ------------------------------------------------------------------
    # 3. Update Draft (PATCH /draft)
    # ------------------------------------------------------------------

    def update_draft(
        self,
        db: Session,
        *,
        membership: FamilyMembership,
        member_id: int,
        import_id: int,
        payload: ImportDraftUpdateRequest,
    ) -> ImportSessionResponse:
        self._ensure_roles(membership, *WRITE_IMPORT_ROLES)
        self._ensure_family_active(membership.family)
        member = self._get_scoped_member(db, membership, member_id)
        session_obj = self._get_scoped_session(
            db,
            family_id=membership.family_id,
            member_id=member.id,
            import_id=import_id,
        )
        self._ensure_session_editable(session_obj)

        review = dict(session_obj.review_payload or {})
        prescription_draft = dict(review.get("prescription") or {})
        med_items = [dict(it) for it in (review.get("items") or [])]
        health_draft = dict(review.get("health_updates") or {})
        member_res = dict(review.get("member_resolution") or {})

        if payload.import_mode is not None:
            session_obj.import_mode = payload.import_mode.value

        if payload.target_prescription_id is not None or "target_prescription_id" in payload.model_fields_set:
            session_obj.target_prescription_id = payload.target_prescription_id

        if payload.confirm_member_match is not None:
            member_res = resolve_member_identity(
                member,
                prescription_draft,
                user_confirmed_override=payload.confirm_member_match,
            )

        if payload.confirm_duplicate_override is not None:
            review["duplicate_acknowledged"] = payload.confirm_duplicate_override

        # Update prescription header fields
        if payload.prescription is not None:
            p_fields = payload.prescription.model_fields_set
            for fn in ("title", "doctor_name", "facility_name", "notes"):
                if fn in p_fields:
                    prescription_draft[fn] = getattr(payload.prescription, fn)
            for dfn in ("issued_at", "start_date", "end_date"):
                if dfn in p_fields:
                    raw_dt = getattr(payload.prescription, dfn)
                    prescription_draft[dfn] = normalize_date(raw_dt) if raw_dt else None
            prescription_draft["user_edited"] = True

        # Update medication & schedule items by row_index
        if payload.items is not None:
            by_row = {it.get("row_index", i): it for i, it in enumerate(med_items)}
            for patch_it in payload.items:
                target = by_row.get(patch_it.row_index)
                if target is None:
                    # Allow adding a new row during review
                    target = {
                        "row_index": patch_it.row_index,
                        "action": "CREATE_NEW",
                        "medication_name": patch_it.medication_name or "",
                        "dose_amount": patch_it.dose_amount or 1.0,
                        "dose_unit": normalize_unit(patch_it.dose_unit),
                        "frequency_per_day": patch_it.frequency_per_day or 1.0,
                        "frequency_text": patch_it.frequency_text,
                        "route": normalize_route(patch_it.route),
                        "quantity": patch_it.quantity or 0.0,
                        "unit": normalize_unit(patch_it.unit or patch_it.dose_unit),
                        "confidence": 1.0,
                        "schedule": {
                            "create_schedule": bool(patch_it.create_schedule),
                            "schedule_times": [],
                            "recurrence_type": "DAILY",
                            "start_date": prescription_draft.get("start_date") or prescription_draft.get("issued_at"),
                            "end_date": prescription_draft.get("end_date"),
                            "reminder_enabled": True,
                            "reminder_before_minutes": 15,
                            "grace_period_minutes": 30,
                        },
                    }
                    med_items.append(target)
                    by_row[patch_it.row_index] = target

                fset = patch_it.model_fields_set
                for key in (
                    "action",
                    "family_medication_id",
                    "catalog_id",
                    "medication_name",
                    "active_ingredient",
                    "strength",
                    "dose_amount",
                    "frequency_per_day",
                    "frequency_text",
                    "instructions",
                    "quantity",
                ):
                    if key in fset:
                        target[key] = getattr(patch_it, key)

                if "dosage_form" in fset and patch_it.dosage_form:
                    target["dosage_form"] = normalize_dosage_form(patch_it.dosage_form)
                if "dose_unit" in fset and patch_it.dose_unit:
                    target["dose_unit"] = normalize_unit(patch_it.dose_unit)
                if "unit" in fset and patch_it.unit:
                    target["unit"] = normalize_unit(patch_it.unit)
                if "route" in fset and patch_it.route:
                    target["route"] = normalize_route(patch_it.route)
                if "expiration_date" in fset:
                    target["expiration_date"] = normalize_date(patch_it.expiration_date)

                sched = dict(target.get("schedule") or {})
                if "create_schedule" in fset and patch_it.create_schedule is not None:
                    sched["create_schedule"] = patch_it.create_schedule
                if "schedule_times" in fset and patch_it.schedule_times is not None:
                    cleaned_times: list[str] = []
                    for t in patch_it.schedule_times:
                        nt = normalize_time_string(str(t))
                        cleaned_times.append(nt if nt else str(t).strip())
                    sched["schedule_times"] = cleaned_times
                if "recurrence_type" in fset and patch_it.recurrence_type:
                    sched["recurrence_type"] = patch_it.recurrence_type
                if "reminder_enabled" in fset and patch_it.reminder_enabled is not None:
                    sched["reminder_enabled"] = patch_it.reminder_enabled
                if "reminder_before_minutes" in fset and patch_it.reminder_before_minutes is not None:
                    sched["reminder_before_minutes"] = patch_it.reminder_before_minutes
                if "grace_period_minutes" in fset and patch_it.grace_period_minutes is not None:
                    sched["grace_period_minutes"] = patch_it.grace_period_minutes
                if "start_date" in fset:
                    sched["start_date"] = normalize_date(patch_it.start_date)
                if "end_date" in fset:
                    sched["end_date"] = normalize_date(patch_it.end_date)

                target["schedule"] = sched
                target["user_edited"] = True
                target["resolution_status"] = (
                    ImportResolutionStatus.SKIPPED.value
                    if target.get("action") == "SKIP"
                    else ImportResolutionStatus.USER_CONFIRMED.value
                )

            # Sync ImportItem records
            for db_item in session_obj.items:
                if db_item.row_index in by_row:
                    updated_row = by_row[db_item.row_index]
                    db_item.edited_data = dict(updated_row)
                    db_item.resolution_status = updated_row.get(
                        "resolution_status", ImportResolutionStatus.USER_CONFIRMED.value
                    )
                    if updated_row.get("family_medication_id"):
                        db_item.matched_entity_type = "FamilyMedication"
                        db_item.matched_entity_id = int(updated_row["family_medication_id"])

        # Update health profile candidates
        if payload.health_updates is not None:
            hfset = payload.health_updates.model_fields_set
            if "confirm_conditions" in hfset:
                health_draft["confirm_conditions"] = payload.health_updates.confirm_conditions
            if "conditions" in hfset and payload.health_updates.conditions is not None:
                health_draft["conditions"] = [
                    c.model_dump(mode="json") for c in payload.health_updates.conditions
                ]
            if "confirm_allergies" in hfset:
                health_draft["confirm_allergies"] = payload.health_updates.confirm_allergies
            if "allergies" in hfset and payload.health_updates.allergies is not None:
                health_draft["allergies"] = [
                    a.model_dump(mode="json") for a in payload.health_updates.allergies
                ]
            if "confirm_drug_reactions" in hfset:
                health_draft["confirm_drug_reactions"] = payload.health_updates.confirm_drug_reactions
            if "drug_reactions" in hfset and payload.health_updates.drug_reactions is not None:
                health_draft["drug_reactions"] = [
                    r.model_dump(mode="json") for r in payload.health_updates.drug_reactions
                ]
            if "general_notes_append" in hfset:
                health_draft["general_notes_append"] = payload.health_updates.general_notes_append

        target_rx = self._get_target_prescription(
            db,
            family_id=membership.family_id,
            member_id=member.id,
            target_prescription_id=session_obj.target_prescription_id,
        )
        prescription_diff = compute_prescription_diff(
            db,
            target_prescription=target_rx,
            prescription_draft=prescription_draft,
            med_items_draft=med_items,
        )

        review["member_resolution"] = member_res
        review["prescription"] = prescription_draft
        review["items"] = med_items
        review["health_updates"] = health_draft
        review["prescription_diff"] = prescription_diff

        session_obj.review_payload = review
        session_obj.reviewed_by_user_id = membership.user_id

        self._rebuild_validation_issues(db, session_obj=session_obj, member=member)

        db.commit()
        db.refresh(session_obj)
        return ImportSessionResponse.from_model(session_obj)

    # ------------------------------------------------------------------
    # 4. Validate Session (POST /validate)
    # ------------------------------------------------------------------

    def validate_session(
        self,
        db: Session,
        *,
        membership: FamilyMembership,
        member_id: int,
        import_id: int,
    ) -> ImportSessionResponse:
        self._ensure_roles(membership, *WRITE_IMPORT_ROLES)
        self._ensure_family_active(membership.family)
        member = self._get_scoped_member(db, membership, member_id)
        session_obj = self._get_scoped_session(
            db,
            family_id=membership.family_id,
            member_id=member.id,
            import_id=import_id,
        )
        self._ensure_session_editable(session_obj)

        self._rebuild_validation_issues(db, session_obj=session_obj, member=member)
        db.commit()
        db.refresh(session_obj)
        return ImportSessionResponse.from_model(session_obj)

    # ------------------------------------------------------------------
    # 5. Commit Session (POST /commit)
    # ------------------------------------------------------------------

    def commit_session(
        self,
        db: Session,
        *,
        membership: FamilyMembership,
        member_id: int,
        import_id: int,
        payload: ImportCommitRequest,
    ) -> ImportSessionResponse:
        self._ensure_roles(membership, *WRITE_IMPORT_ROLES)
        self._ensure_family_active(membership.family)
        member = self._get_scoped_member(db, membership, member_id)
        session_obj = self._get_scoped_session(
            db,
            family_id=membership.family_id,
            member_id=member.id,
            import_id=import_id,
        )
        self._ensure_session_editable(session_obj)

        # If user chose not to create schedules on commit, disable schedule validation errors first
        if not payload.confirm_schedule_creation:
            review = dict(session_obj.review_payload or {})
            items = [dict(it) for it in (review.get("items") or [])]
            for it in items:
                sched = dict(it.get("schedule") or {})
                sched["create_schedule"] = False
                it["schedule"] = sched
            review["items"] = items
            session_obj.review_payload = review

        # Re-run validation before commit
        self._rebuild_validation_issues(db, session_obj=session_obj, member=member)

        blocking_or_errors = [
            iss
            for iss in session_obj.validation_issues
            if iss.severity in {ValidationSeverity.BLOCKING.value, ValidationSeverity.ERROR.value}
            and not iss.is_resolved
        ]
        if blocking_or_errors:
            first_msg = blocking_or_errors[0].message
            db.commit()
            raise ImportValidationBlockedError(
                f"Không thể xác nhận lưu đơn thuốc khi còn lỗi chưa xử lý: {first_msg}"
            )

        self.commit_service.commit(
            db,
            session_obj=session_obj,
            user_id=membership.user_id,
            payload=payload,
        )
        db.refresh(session_obj)
        return ImportSessionResponse.from_model(session_obj)

    # ------------------------------------------------------------------
    # 6. Reject Session (POST /reject)
    # ------------------------------------------------------------------

    def reject_session(
        self,
        db: Session,
        *,
        membership: FamilyMembership,
        member_id: int,
        import_id: int,
        payload: ImportRejectRequest | None = None,
    ) -> ImportSessionResponse:
        self._ensure_roles(membership, *WRITE_IMPORT_ROLES)
        self._ensure_family_active(membership.family)
        member = self._get_scoped_member(db, membership, member_id)
        session_obj = self._get_scoped_session(
            db,
            family_id=membership.family_id,
            member_id=member.id,
            import_id=import_id,
        )
        if session_obj.status == ImportStatus.COMMITTED.value:
            raise ImportAlreadyCommittedError("Phiên nhập đã được lưu, không thể hủy bỏ.")

        session_obj.status = ImportStatus.REJECTED.value
        session_obj.reviewed_by_user_id = membership.user_id
        if payload and payload.reason:
            review = dict(session_obj.review_payload or {})
            review["reject_reason"] = payload.reason
            session_obj.review_payload = review

        db.commit()
        db.refresh(session_obj)
        return ImportSessionResponse.from_model(session_obj)

    # ------------------------------------------------------------------
    # 7. Template Download
    # ------------------------------------------------------------------

    @staticmethod
    def get_template_xlsx_bytes() -> bytes:
        return generate_template_xlsx()

    # ------------------------------------------------------------------
    # Internal Helpers
    # ------------------------------------------------------------------

    def _rebuild_validation_issues(
        self,
        db: Session,
        *,
        session_obj: ImportSession,
        member: FamilyMember,
    ) -> None:
        self.repository.clear_validation_issues(db, session_obj.id)

        review = dict(session_obj.review_payload or {})
        member_res = dict(review.get("member_resolution") or {})
        if not member_res:
            member_res = resolve_member_identity(
                member,
                review.get("prescription") or {},
            )
            review["member_resolution"] = member_res
            session_obj.review_payload = review

        prescription_draft = dict(review.get("prescription") or {})
        med_items = list(review.get("items") or [])
        health_draft = dict(review.get("health_updates") or {})

        target_rx = self._get_target_prescription(
            db,
            family_id=session_obj.family_id,
            member_id=session_obj.member_id,
            target_prescription_id=session_obj.target_prescription_id,
        )

        all_issue_specs: list[dict[str, Any]] = []
        all_issue_specs.extend(
            validate_prescription_header(
                member_resolution=member_res,
                prescription_draft=prescription_draft,
                import_mode=session_obj.import_mode,
                target_prescription=target_rx,
                is_duplicate=session_obj.is_duplicate,
                duplicate_of_import_id=session_obj.duplicate_of_import_id,
                duplicate_acknowledged=bool(review.get("duplicate_acknowledged", False)),
            )
        )
        all_issue_specs.extend(validate_medication_items(med_items))
        all_issue_specs.extend(validate_schedule_candidates(med_items))
        all_issue_specs.extend(
            validate_health_candidates(
                db,
                member_id=session_obj.member_id,
                health_draft=health_draft,
            )
        )

        has_blocking_or_error = False
        for spec in all_issue_specs:
            sev = spec["severity"]
            if sev in {ValidationSeverity.BLOCKING.value, ValidationSeverity.ERROR.value}:
                has_blocking_or_error = True
            issue_model = ImportValidationIssue(
                import_session_id=session_obj.id,
                import_item_id=spec.get("import_item_id"),
                severity=sev,
                code=spec["code"],
                field_path=spec["field_path"],
                message=spec["message"],
                suggested_fix=spec.get("suggested_fix"),
                is_resolved=False,
            )
            self.repository.add_validation_issue(db, issue_model)

        if session_obj.status not in {ImportStatus.COMMITTED.value, ImportStatus.REJECTED.value}:
            session_obj.status = (
                ImportStatus.REVIEW_REQUIRED.value
                if has_blocking_or_error
                else ImportStatus.READY_TO_COMMIT.value
            )
        db.flush()
        db.expire(session_obj, ["validation_issues"])

    @staticmethod
    def _validate_file(
        *,
        filename: str,
        file_bytes: bytes,
        explicit_source_type: str | None,
    ) -> tuple[str, str]:
        if not filename or "." not in filename:
            raise ImportUnsupportedFileError("Tệp tải lên phải có phần mở rộng hợp lệ (.jpg, .png, .pdf, .xlsx, .csv).")

        ext = filename.rsplit(".", 1)[-1].lower().strip()
        if ext not in ALLOWED_EXTENSIONS:
            raise ImportUnsupportedFileError(
                f"Định dạng tệp '.{ext}' không được hỗ trợ. Chỉ chấp nhận: JPG, JPEG, PNG, PDF, XLSX, CSV."
            )

        if not file_bytes:
            raise ImportUnsupportedFileError("Tệp tải lên bị rỗng (0 bytes).")

        max_size = MAX_PDF_BYTES if ext == "pdf" else MAX_OTHER_BYTES
        if len(file_bytes) > max_size:
            raise ImportUnsupportedFileError(
                f"Kích thước tệp vượt quá giới hạn cho phép ({max_size // (1024 * 1024)}MB)."
            )

        inferred_type = ALLOWED_EXTENSIONS[ext].value
        if explicit_source_type and explicit_source_type in {t.value for t in ImportSourceType}:
            # Keep file-extension-derived type if explicit type conflicts with Excel/OCR family
            if ext in {"xlsx", "csv"}:
                return inferred_type, ext
            return explicit_source_type, ext
        return inferred_type, ext

    @staticmethod
    def _save_private_file(
        *,
        family_id: int,
        member_id: int,
        ext: str,
        file_bytes: bytes,
    ) -> str:
        target_dir = STORAGE_ROOT / f"family_{family_id}" / f"member_{member_id}"
        target_dir.mkdir(parents=True, exist_ok=True)
        unique_name = f"{uuid.uuid4().hex}.{ext}"
        full_path = target_dir / unique_name
        full_path.write_bytes(file_bytes)
        return str(full_path).replace("\\", "/")

    def _get_scoped_member(
        self,
        db: Session,
        membership: FamilyMembership,
        member_id: int,
    ) -> FamilyMember:
        member = self.member_repository.get_member(
            db,
            family_id=membership.family_id,
            member_id=member_id,
        )
        if member is None:
            raise MemberNotFoundError("Không tìm thấy thành viên trong gia đình.")
        return member

    def _get_scoped_session(
        self,
        db: Session,
        *,
        family_id: int,
        member_id: int,
        import_id: int,
    ) -> ImportSession:
        session_obj = self.repository.get_session(
            db,
            family_id=family_id,
            member_id=member_id,
            import_id=import_id,
        )
        if session_obj is None:
            raise ImportSessionNotFoundError("Không tìm thấy phiên nhập đơn thuốc.")
        return session_obj

    @staticmethod
    def _get_target_prescription(
        db: Session,
        *,
        family_id: int,
        member_id: int,
        target_prescription_id: int | None,
    ) -> Prescription | None:
        if not target_prescription_id:
            return None
        return db.scalars(
            select(Prescription).where(
                Prescription.id == target_prescription_id,
                Prescription.family_id == family_id,
                Prescription.member_id == member_id,
            )
        ).first()

    @staticmethod
    def _ensure_session_editable(session_obj: ImportSession) -> None:
        if session_obj.status in {ImportStatus.COMMITTED.value, ImportStatus.REJECTED.value}:
            raise ImportAlreadyCommittedError(
                f"Phiên nhập đang ở trạng thái {session_obj.status}, không thể chỉnh sửa hoặc lưu lại."
            )

    @staticmethod
    def _ensure_roles(
        membership: FamilyMembership,
        *allowed_roles: FamilyRole,
    ) -> None:
        allowed_values = {role.value for role in allowed_roles}
        if membership.role not in allowed_values:
            raise InsufficientFamilyPermissionError(
                "Bạn không có quyền thực hiện thao tác nhập đơn thuốc (yêu cầu OWNER, ADMIN hoặc CAREGIVER)."
            )

    @staticmethod
    def _ensure_family_active(family: Family) -> None:
        if family.status != FamilyStatus.ACTIVE.value:
            raise FamilyArchivedError("Gia đình đang ở trạng thái lưu trữ (ARCHIVED).")

