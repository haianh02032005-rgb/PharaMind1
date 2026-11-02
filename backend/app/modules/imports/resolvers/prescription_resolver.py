from typing import Any

from sqlalchemy.orm import Session

from backend.app.models.prescription import Prescription
from backend.app.modules.imports.normalizers.medication_normalizer import (
    normalize_medication_key,
)


def compute_prescription_diff(
    db: Session,
    *,
    target_prescription: Prescription | None,
    prescription_draft: dict[str, Any],
    med_items_draft: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Compute structured diff when updating an existing prescription (§12)."""
    if target_prescription is None:
        return None

    meta_changes: dict[str, dict[str, Any]] = {}
    for field in ("title", "doctor_name", "facility_name", "issued_at", "start_date", "end_date", "notes"):
        old_val = getattr(target_prescription, field, None)
        old_str = old_val.isoformat() if hasattr(old_val, "isoformat") else old_val
        new_val = prescription_draft.get(field)
        if new_val and str(new_val) != str(old_str or ""):
            meta_changes[field] = {"previous": old_str, "proposed": new_val}

    existing_by_med_id: dict[int, Any] = {}
    existing_by_name: dict[str, Any] = {}
    for existing_item in target_prescription.items:
        existing_by_med_id[existing_item.family_medication_id] = existing_item
        if existing_item.family_medication and existing_item.family_medication.catalog:
            key = normalize_medication_key(existing_item.family_medication.catalog.name)
            if key:
                existing_by_name[key] = existing_item

    added_items: list[dict[str, Any]] = []
    updated_items: list[dict[str, Any]] = []
    unchanged_items: list[dict[str, Any]] = []
    matched_existing_ids: set[int] = set()

    for draft_item in med_items_draft:
        if draft_item.get("action") == "SKIP":
            continue
        fam_med_id = draft_item.get("family_medication_id")
        med_key = normalize_medication_key(draft_item.get("medication_name"))

        existing_match = None
        if fam_med_id and fam_med_id in existing_by_med_id:
            existing_match = existing_by_med_id[fam_med_id]
        elif med_key and med_key in existing_by_name:
            existing_match = existing_by_name[med_key]

        if existing_match is None:
            added_items.append(
                {
                    "row_index": draft_item.get("row_index"),
                    "medication_name": draft_item.get("medication_name"),
                    "dose_amount": draft_item.get("dose_amount"),
                    "dose_unit": draft_item.get("dose_unit"),
                    "frequency_per_day": draft_item.get("frequency_per_day"),
                    "frequency_text": draft_item.get("frequency_text"),
                    "instructions": draft_item.get("instructions"),
                }
            )
        else:
            matched_existing_ids.add(existing_match.id)
            field_diffs: dict[str, dict[str, Any]] = {}
            for f in ("dose_amount", "dose_unit", "frequency_per_day", "frequency_text", "route", "instructions"):
                old_v = getattr(existing_match, f, None)
                new_v = draft_item.get(f)
                if new_v is not None and str(old_v) != str(new_v):
                    field_diffs[f] = {"previous": old_v, "proposed": new_v}

            if field_diffs:
                updated_items.append(
                    {
                        "row_index": draft_item.get("row_index"),
                        "existing_item_id": existing_match.id,
                        "medication_name": draft_item.get("medication_name"),
                        "changes": field_diffs,
                    }
                )
            else:
                unchanged_items.append(
                    {
                        "row_index": draft_item.get("row_index"),
                        "existing_item_id": existing_match.id,
                        "medication_name": draft_item.get("medication_name"),
                    }
                )

    retained_existing_items: list[dict[str, Any]] = []
    for existing_item in target_prescription.items:
        if existing_item.id not in matched_existing_ids:
            med_title = (
                existing_item.family_medication.catalog.name
                if existing_item.family_medication and existing_item.family_medication.catalog
                else f"Medication #{existing_item.family_medication_id}"
            )
            retained_existing_items.append(
                {
                    "existing_item_id": existing_item.id,
                    "medication_name": med_title,
                    "note": "Được giữ nguyên (không tự động xóa thuốc cũ theo quy tắc an toàn §12.2)",
                }
            )

    return {
        "target_prescription_id": target_prescription.id,
        "target_prescription_title": target_prescription.title,
        "target_prescription_status": target_prescription.status,
        "metadata_changes": meta_changes,
        "added_items": added_items,
        "updated_items": updated_items,
        "unchanged_items": unchanged_items,
        "retained_existing_items": retained_existing_items,
    }

