from datetime import datetime, time, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.allergy_profile import AllergyProfile
from backend.app.models.drug_reaction_history import DrugReactionHistory
from backend.app.models.family_medication import FamilyMedication
from backend.app.models.health_profile import HealthProfile
from backend.app.models.import_entity_link import ImportEntityLink
from backend.app.models.import_session import ImportSession
from backend.app.models.medical_condition import MedicalCondition
from backend.app.models.medication_catalog import MedicationCatalog
from backend.app.models.medication_schedule import MedicationSchedule
from backend.app.models.member_medication import MemberMedication
from backend.app.models.prescription import Prescription
from backend.app.models.prescription_item import PrescriptionItem
from backend.app.models.schedule_time import ScheduleTime
from backend.app.modules.imports.enums import (
    ImportEntityAction,
    ImportMode,
    ImportSourceType,
    ImportStatus,
)
from backend.app.modules.imports.exceptions import (
    ImportTransactionRollbackError,
    ImportValidationBlockedError,
)
from backend.app.modules.imports.normalizers.date_normalizer import (
    normalize_time_string,
    parse_iso_date,
)
from backend.app.modules.imports.schema import ImportCommitRequest
from backend.app.modules.medications.enums import MedicationStatus
from backend.app.modules.prescriptions.enums import PrescriptionStatus


class ImportCommitService:
    def commit(
        self,
        db: Session,
        *,
        session_obj: ImportSession,
        user_id: int,
        payload: ImportCommitRequest,
    ) -> dict[str, Any]:
        """Execute the 10-step atomic commit plan (§23). Rolls back all writes if any error occurs."""
        if payload.confirm_member_id != session_obj.member_id:
            raise ImportValidationBlockedError(
                "confirm_member_id không khớp với thành viên của phiên nhập."
            )

        review = dict(session_obj.review_payload or {})
        prescription_draft = dict(review.get("prescription") or {})
        med_items = list(review.get("items") or [])
        health_draft = dict(review.get("health_updates") or {})
        import_mode = payload.confirm_import_mode.value if payload.confirm_import_mode else session_obj.import_mode

        catalog_source = (
            "OCR_IMPORT"
            if session_obj.source_type
            in {ImportSourceType.OCR_IMAGE.value, ImportSourceType.OCR_PDF.value}
            else "EXCEL_IMPORT"
        )

        created_counts = {
            "catalogs_created": 0,
            "family_medications_created": 0,
            "family_medications_linked": 0,
            "member_medications_linked": 0,
            "prescriptions_created": 0,
            "prescriptions_updated": 0,
            "prescription_items_created": 0,
            "prescription_items_updated": 0,
            "schedules_created": 0,
            "conditions_created": 0,
            "allergies_created": 0,
            "drug_reactions_created": 0,
        }

        try:
            # Step 1: Resolve or create Target Prescription (unless CREATE_MEDICATION_ONLY)
            prescription: Prescription | None = None
            if import_mode == ImportMode.UPDATE_EXISTING_PRESCRIPTION.value:
                target_id = session_obj.target_prescription_id
                if not target_id:
                    raise ImportValidationBlockedError(
                        "Thiếu target_prescription_id khi cập nhật đơn thuốc hiện có."
                    )
                prescription = db.scalars(
                    select(Prescription).where(
                        Prescription.id == target_id,
                        Prescription.family_id == session_obj.family_id,
                        Prescription.member_id == session_obj.member_id,
                    )
                ).first()
                if prescription is None:
                    raise ImportValidationBlockedError(
                        "Không tìm thấy đơn thuốc hiện có để cập nhật."
                    )
                prev_rx_snap = {
                    "title": prescription.title,
                    "doctor_name": prescription.doctor_name,
                    "facility_name": prescription.facility_name,
                    "issued_at": prescription.issued_at.isoformat() if prescription.issued_at else None,
                    "start_date": prescription.start_date.isoformat() if prescription.start_date else None,
                    "end_date": prescription.end_date.isoformat() if prescription.end_date else None,
                    "notes": prescription.notes,
                }
                if prescription_draft.get("title"):
                    prescription.title = prescription_draft["title"]
                if prescription_draft.get("doctor_name"):
                    prescription.doctor_name = prescription_draft["doctor_name"]
                if prescription_draft.get("facility_name"):
                    prescription.facility_name = prescription_draft["facility_name"]
                if prescription_draft.get("issued_at"):
                    prescription.issued_at = parse_iso_date(prescription_draft["issued_at"])
                if prescription_draft.get("start_date"):
                    prescription.start_date = parse_iso_date(prescription_draft["start_date"])
                if prescription_draft.get("end_date"):
                    prescription.end_date = parse_iso_date(prescription_draft["end_date"])
                if prescription_draft.get("notes"):
                    prescription.notes = prescription_draft["notes"]
                db.flush()
                created_counts["prescriptions_updated"] += 1
                self._record_link(
                    db,
                    session_id=session_obj.id,
                    entity_type="Prescription",
                    entity_id=prescription.id,
                    action=ImportEntityAction.UPDATED.value,
                    previous_snapshot=prev_rx_snap,
                    new_snapshot={
                        "title": prescription.title,
                        "doctor_name": prescription.doctor_name,
                        "facility_name": prescription.facility_name,
                    },
                )
            elif import_mode == ImportMode.CREATE_NEW_PRESCRIPTION.value:
                prescription = Prescription(
                    family_id=session_obj.family_id,
                    member_id=session_obj.member_id,
                    title=prescription_draft.get("title") or "Đơn thuốc nhập từ tài liệu",
                    doctor_name=prescription_draft.get("doctor_name"),
                    facility_name=prescription_draft.get("facility_name"),
                    issued_at=parse_iso_date(prescription_draft.get("issued_at")),
                    start_date=parse_iso_date(prescription_draft.get("start_date"))
                    or parse_iso_date(prescription_draft.get("issued_at")),
                    end_date=parse_iso_date(prescription_draft.get("end_date")),
                    status=PrescriptionStatus.ACTIVE.value,
                    notes=prescription_draft.get("notes"),
                )
                db.add(prescription)
                db.flush()
                created_counts["prescriptions_created"] += 1
                self._record_link(
                    db,
                    session_id=session_obj.id,
                    entity_type="Prescription",
                    entity_id=prescription.id,
                    action=ImportEntityAction.CREATED.value,
                    previous_snapshot=None,
                    new_snapshot={
                        "id": prescription.id,
                        "title": prescription.title,
                        "member_id": prescription.member_id,
                    },
                )

            # Step 2-7: Process each active medication item
            for item in med_items:
                if item.get("action") == "SKIP":
                    continue

                # Step 2: Resolve or create MedicationCatalog
                catalog_id = item.get("catalog_id")
                catalog: MedicationCatalog | None = None
                if catalog_id:
                    catalog = db.get(MedicationCatalog, int(catalog_id))

                if catalog is None:
                    catalog = MedicationCatalog(
                        name=item.get("medication_name") or "Thuốc nhập đơn",
                        active_ingredient=item.get("active_ingredient"),
                        strength=item.get("strength"),
                        dosage_form=item.get("dosage_form") or "TABLET",
                        manufacturer=item.get("manufacturer"),
                        description=item.get("instructions"),
                        source=catalog_source,
                    )
                    db.add(catalog)
                    db.flush()
                    created_counts["catalogs_created"] += 1
                    self._record_link(
                        db,
                        session_id=session_obj.id,
                        entity_type="MedicationCatalog",
                        entity_id=catalog.id,
                        action=ImportEntityAction.CREATED.value,
                        previous_snapshot=None,
                        new_snapshot={"id": catalog.id, "name": catalog.name, "source": catalog_source},
                    )

                # Step 3: Resolve or create FamilyMedication
                fam_med_id = item.get("family_medication_id")
                fam_med: FamilyMedication | None = None
                if fam_med_id and item.get("action") == "LINK_EXISTING":
                    fam_med = db.scalars(
                        select(FamilyMedication).where(
                            FamilyMedication.id == int(fam_med_id),
                            FamilyMedication.family_id == session_obj.family_id,
                        )
                    ).first()

                if fam_med is not None:
                    created_counts["family_medications_linked"] += 1
                    self._record_link(
                        db,
                        session_id=session_obj.id,
                        entity_type="FamilyMedication",
                        entity_id=fam_med.id,
                        action=ImportEntityAction.LINKED.value,
                        previous_snapshot={"quantity": fam_med.quantity},
                        new_snapshot={"quantity": fam_med.quantity},
                    )
                else:
                    qty = float(item.get("quantity") or 0.0)
                    fam_med = FamilyMedication(
                        family_id=session_obj.family_id,
                        catalog_id=catalog.id,
                        quantity=qty,
                        unit=item.get("unit") or item.get("dose_unit") or "tablet",
                        expiration_date=parse_iso_date(item.get("expiration_date")),
                        status=MedicationStatus.ACTIVE.value,
                        notes=item.get("instructions"),
                    )
                    db.add(fam_med)
                    db.flush()
                    created_counts["family_medications_created"] += 1
                    self._record_link(
                        db,
                        session_id=session_obj.id,
                        entity_type="FamilyMedication",
                        entity_id=fam_med.id,
                        action=ImportEntityAction.CREATED.value,
                        previous_snapshot=None,
                        new_snapshot={
                            "id": fam_med.id,
                            "catalog_id": catalog.id,
                            "quantity": fam_med.quantity,
                            "unit": fam_med.unit,
                        },
                    )

                # Step 4: Ensure MemberMedication link exists
                member_link = db.scalars(
                    select(MemberMedication).where(
                        MemberMedication.member_id == session_obj.member_id,
                        MemberMedication.family_medication_id == fam_med.id,
                    )
                ).first()
                if member_link is None:
                    member_link = MemberMedication(
                        member_id=session_obj.member_id,
                        family_medication_id=fam_med.id,
                    )
                    db.add(member_link)
                    db.flush()
                    created_counts["member_medications_linked"] += 1
                    self._record_link(
                        db,
                        session_id=session_obj.id,
                        entity_type="MemberMedication",
                        entity_id=member_link.id,
                        action=ImportEntityAction.CREATED.value,
                        previous_snapshot=None,
                        new_snapshot={
                            "member_id": session_obj.member_id,
                            "family_medication_id": fam_med.id,
                        },
                    )

                # Step 5-6: Create or update PrescriptionItem (if prescription mode)
                rx_item: PrescriptionItem | None = None
                if prescription is not None:
                    existing_rx_item = db.scalars(
                        select(PrescriptionItem).where(
                            PrescriptionItem.prescription_id == prescription.id,
                            PrescriptionItem.family_medication_id == fam_med.id,
                        )
                    ).first()

                    if existing_rx_item is not None:
                        prev_item_snap = {
                            "dose_amount": existing_rx_item.dose_amount,
                            "dose_unit": existing_rx_item.dose_unit,
                            "frequency_per_day": existing_rx_item.frequency_per_day,
                            "frequency_text": existing_rx_item.frequency_text,
                            "route": existing_rx_item.route,
                            "instructions": existing_rx_item.instructions,
                        }
                        existing_rx_item.dose_amount = float(item.get("dose_amount") or 1.0)
                        existing_rx_item.dose_unit = item.get("dose_unit") or "tablet"
                        existing_rx_item.frequency_per_day = (
                            float(item["frequency_per_day"])
                            if item.get("frequency_per_day") is not None
                            else None
                        )
                        existing_rx_item.frequency_text = item.get("frequency_text")
                        existing_rx_item.route = item.get("route") or "ORAL"
                        existing_rx_item.instructions = item.get("instructions")
                        db.flush()
                        rx_item = existing_rx_item
                        created_counts["prescription_items_updated"] += 1
                        self._record_link(
                            db,
                            session_id=session_obj.id,
                            entity_type="PrescriptionItem",
                            entity_id=rx_item.id,
                            action=ImportEntityAction.UPDATED.value,
                            previous_snapshot=prev_item_snap,
                            new_snapshot={
                                "dose_amount": rx_item.dose_amount,
                                "dose_unit": rx_item.dose_unit,
                                "frequency_per_day": rx_item.frequency_per_day,
                            },
                        )
                    else:
                        rx_item = PrescriptionItem(
                            prescription_id=prescription.id,
                            family_medication_id=fam_med.id,
                            dose_amount=float(item.get("dose_amount") or 1.0),
                            dose_unit=item.get("dose_unit") or "tablet",
                            frequency_per_day=(
                                float(item["frequency_per_day"])
                                if item.get("frequency_per_day") is not None
                                else None
                            ),
                            frequency_text=item.get("frequency_text"),
                            route=item.get("route") or "ORAL",
                            instructions=item.get("instructions"),
                        )
                        db.add(rx_item)
                        db.flush()
                        created_counts["prescription_items_created"] += 1
                        self._record_link(
                            db,
                            session_id=session_obj.id,
                            entity_type="PrescriptionItem",
                            entity_id=rx_item.id,
                            action=ImportEntityAction.CREATED.value,
                            previous_snapshot=None,
                            new_snapshot={
                                "id": rx_item.id,
                                "prescription_id": prescription.id,
                                "family_medication_id": fam_med.id,
                                "dose_amount": rx_item.dose_amount,
                                "dose_unit": rx_item.dose_unit,
                            },
                        )

                # Step 7: Create MedicationSchedule + ScheduleTime if confirmed
                sched_cfg = item.get("schedule") or {}
                if (
                    payload.confirm_schedule_creation
                    and rx_item is not None
                    and sched_cfg.get("create_schedule", False)
                ):
                    sched_times = [
                        normalize_time_string(str(t))
                        for t in (sched_cfg.get("schedule_times") or [])
                    ]
                    valid_times = [t for t in sched_times if t]
                    start_dt = (
                        parse_iso_date(sched_cfg.get("start_date"))
                        or (prescription.start_date if prescription else None)
                        or parse_iso_date(prescription_draft.get("issued_at"))
                    )
                    end_dt = parse_iso_date(sched_cfg.get("end_date")) or (
                        prescription.end_date if prescription else None
                    )
                    if valid_times and start_dt:
                        med_schedule = MedicationSchedule(
                            family_id=session_obj.family_id,
                            member_id=session_obj.member_id,
                            prescription_item_id=rx_item.id,
                            family_medication_id=fam_med.id,
                            recurrence_type=sched_cfg.get("recurrence_type") or "DAILY",
                            start_date=start_dt,
                            end_date=end_dt,
                            reminder_enabled=bool(sched_cfg.get("reminder_enabled", True)),
                            reminder_before_minutes=int(
                                sched_cfg.get("reminder_before_minutes", 15)
                            ),
                            grace_period_minutes=int(
                                sched_cfg.get("grace_period_minutes", 30)
                            ),
                            status="ACTIVE",
                            notes=item.get("instructions"),
                        )
                        db.add(med_schedule)
                        db.flush()

                        for t_str in sorted(set(valid_times)):
                            hh, mm = [int(p) for p in t_str.split(":")]
                            st = ScheduleTime(
                                schedule_id=med_schedule.id,
                                time_of_day=time(hh, mm),
                            )
                            db.add(st)
                        db.flush()
                        created_counts["schedules_created"] += 1
                        self._record_link(
                            db,
                            session_id=session_obj.id,
                            entity_type="MedicationSchedule",
                            entity_id=med_schedule.id,
                            action=ImportEntityAction.CREATED.value,
                            previous_snapshot=None,
                            new_snapshot={
                                "id": med_schedule.id,
                                "prescription_item_id": rx_item.id,
                                "times": sorted(set(valid_times)),
                            },
                        )

            # Simulated failure hook for testing atomic transaction rollback (§32.9)
            if payload.simulate_failure:
                raise RuntimeError("Simulated commit failure for transaction rollback test")

            # Step 8: Optional HealthProfile & Condition/Allergy/DrugReaction updates (§14)
            if payload.confirm_health_updates:
                self._commit_health_updates(
                    db,
                    session_obj=session_obj,
                    health_draft=health_draft,
                    created_counts=created_counts,
                )

            # Step 10: Mark ImportSession as COMMITTED
            now = datetime.now(timezone.utc)
            session_obj.status = ImportStatus.COMMITTED.value
            session_obj.import_mode = import_mode
            session_obj.committed_by_user_id = user_id
            session_obj.committed_at = now
            session_obj.commit_summary = {
                **created_counts,
                "prescription_id": prescription.id if prescription else None,
                "committed_at": now.isoformat(),
            }
            db.flush()
            db.commit()
            db.refresh(session_obj)
            return session_obj.commit_summary

        except ImportValidationBlockedError:
            db.rollback()
            raise
        except Exception as exc:
            db.rollback()
            raise ImportTransactionRollbackError(
                f"Quá trình lưu đơn thuốc gặp lỗi và đã được hoàn tác an toàn: {exc}"
            ) from exc

    def _commit_health_updates(
        self,
        db: Session,
        *,
        session_obj: ImportSession,
        health_draft: dict[str, Any],
        created_counts: dict[str, int],
    ) -> None:
        member_id = session_obj.member_id

        # Conditions
        if health_draft.get("confirm_conditions", True):
            for cond in health_draft.get("conditions") or []:
                if not cond.get("confirmed", True):
                    continue
                name = (cond.get("name") or "").strip()
                if not name:
                    continue
                mc = MedicalCondition(
                    member_id=member_id,
                    name=name,
                    diagnosed_at=parse_iso_date(cond.get("diagnosed_at")),
                    status=cond.get("status") or "ACTIVE",
                    notes=cond.get("notes") or "Nhập từ đơn thuốc",
                )
                db.add(mc)
                db.flush()
                created_counts["conditions_created"] += 1
                self._record_link(
                    db,
                    session_id=session_obj.id,
                    entity_type="MedicalCondition",
                    entity_id=mc.id,
                    action=ImportEntityAction.CREATED.value,
                    previous_snapshot=None,
                    new_snapshot={"id": mc.id, "name": mc.name},
                )

        # Allergies (Never auto-delete existing allergies!)
        if health_draft.get("confirm_allergies", True):
            for al in health_draft.get("allergies") or []:
                if not al.get("confirmed", True):
                    continue
                allergen = (al.get("allergen") or "").strip()
                if not allergen:
                    continue
                ap = AllergyProfile(
                    member_id=member_id,
                    allergen=allergen,
                    allergy_type=al.get("allergy_type") or "DRUG",
                    severity=al.get("severity") or "MODERATE",
                    reaction_description=al.get("reaction_description"),
                    source="PRESCRIPTION_IMPORT",
                    notes=al.get("notes"),
                )
                db.add(ap)
                db.flush()
                created_counts["allergies_created"] += 1
                self._record_link(
                    db,
                    session_id=session_obj.id,
                    entity_type="AllergyProfile",
                    entity_id=ap.id,
                    action=ImportEntityAction.CREATED.value,
                    previous_snapshot=None,
                    new_snapshot={"id": ap.id, "allergen": ap.allergen},
                )

        # Drug Reaction History (Never auto-convert to AllergyProfile!)
        if health_draft.get("confirm_drug_reactions", True):
            for rx in health_draft.get("drug_reactions") or []:
                if not rx.get("confirmed", True):
                    continue
                drug_name = (rx.get("drug_name") or "").strip()
                reaction_txt = (rx.get("reaction") or "").strip()
                if not drug_name or not reaction_txt:
                    continue
                dr = DrugReactionHistory(
                    member_id=member_id,
                    drug_name=drug_name,
                    active_ingredient=rx.get("active_ingredient"),
                    reaction=reaction_txt,
                    severity=rx.get("severity") or "MODERATE",
                    occurred_at=parse_iso_date(rx.get("occurred_at")),
                    confirmed_by_professional=True,
                    notes=rx.get("notes") or "Nhập từ đơn thuốc",
                )
                db.add(dr)
                db.flush()
                created_counts["drug_reactions_created"] += 1
                self._record_link(
                    db,
                    session_id=session_obj.id,
                    entity_type="DrugReactionHistory",
                    entity_id=dr.id,
                    action=ImportEntityAction.CREATED.value,
                    previous_snapshot=None,
                    new_snapshot={"id": dr.id, "drug_name": dr.drug_name, "reaction": dr.reaction},
                )

        # General notes append on HealthProfile if provided
        notes_append = (health_draft.get("general_notes_append") or "").strip()
        if notes_append:
            hp = db.scalars(
                select(HealthProfile).where(HealthProfile.member_id == member_id)
            ).first()
            if hp is None:
                hp = HealthProfile(member_id=member_id, general_notes=notes_append)
                db.add(hp)
                db.flush()
                self._record_link(
                    db,
                    session_id=session_obj.id,
                    entity_type="HealthProfile",
                    entity_id=hp.id,
                    action=ImportEntityAction.CREATED.value,
                    previous_snapshot=None,
                    new_snapshot={"general_notes": hp.general_notes},
                )
            else:
                prev_notes = hp.general_notes
                hp.general_notes = (
                    f"{prev_notes}\n{notes_append}".strip() if prev_notes else notes_append
                )
                db.flush()
                self._record_link(
                    db,
                    session_id=session_obj.id,
                    entity_type="HealthProfile",
                    entity_id=hp.id,
                    action=ImportEntityAction.UPDATED.value,
                    previous_snapshot={"general_notes": prev_notes},
                    new_snapshot={"general_notes": hp.general_notes},
                )

    @staticmethod
    def _record_link(
        db: Session,
        *,
        session_id: int,
        entity_type: str,
        entity_id: int,
        action: str,
        previous_snapshot: dict[str, Any] | None,
        new_snapshot: dict[str, Any] | None,
    ) -> None:
        link = ImportEntityLink(
            import_session_id=session_id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            previous_snapshot=previous_snapshot,
            new_snapshot=new_snapshot,
        )
        db.add(link)
        db.flush()

