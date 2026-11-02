from typing import Any

from backend.app.modules.imports.normalizers.date_normalizer import normalize_date


def parse_prescription_meta(raw_meta: dict[str, Any]) -> dict[str, Any]:
    """Normalize prescription header metadata."""
    issued_at = normalize_date(raw_meta.get("issued_at"))
    start_date = normalize_date(raw_meta.get("start_date")) or issued_at
    end_date = normalize_date(raw_meta.get("end_date"))

    return {
        "member_name": (raw_meta.get("member_name") or "").strip() or None,
        "member_identifier": (raw_meta.get("member_identifier") or "").strip() or None,
        "title": (raw_meta.get("prescription_title") or raw_meta.get("title") or "").strip() or "Đơn thuốc nhập từ tài liệu",
        "doctor_name": (raw_meta.get("doctor_name") or "").strip() or None,
        "facility_name": (raw_meta.get("facility_name") or "").strip() or None,
        "issued_at": issued_at,
        "start_date": start_date,
        "end_date": end_date,
        "status": "ACTIVE",
        "notes": (raw_meta.get("notes") or raw_meta.get("diagnosis_notes") or "").strip() or None,
        "diagnosis_notes": (raw_meta.get("diagnosis_notes") or "").strip() or None,
        "allergy_notes": (raw_meta.get("allergy_notes") or "").strip() or None,
        "adverse_reaction_notes": (raw_meta.get("adverse_reaction_notes") or "").strip() or None,
        "field_confidences": raw_meta.get("field_confidences") or {},
    }

