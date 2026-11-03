from typing import Any

from backend.app.modules.imports.normalizers.date_normalizer import normalize_date
from backend.app.modules.imports.normalizers.dosage_normalizer import (
    normalize_dosage_form,
    normalize_route,
    normalize_unit,
    parse_frequency_per_day,
)
from backend.app.modules.imports.normalizers.medication_normalizer import (
    extract_strength_from_name,
    infer_active_ingredient,
)


def parse_medication_item(raw_item: dict[str, Any], row_index: int) -> dict[str, Any]:
    raw_name = (raw_item.get("medication_name") or "").strip()
    _, extracted_strength = extract_strength_from_name(raw_name)
    strength = (raw_item.get("strength") or "").strip() or extracted_strength
    active_ingredient = infer_active_ingredient(
        raw_name,
        raw_item.get("active_ingredient"),
    )

    dose_unit_raw = raw_item.get("dose_unit") or raw_item.get("unit")
    dose_unit = normalize_unit(dose_unit_raw) if dose_unit_raw else None
    unit_raw = raw_item.get("unit") or dose_unit_raw
    unit = normalize_unit(unit_raw) if unit_raw else None
    dosage_form = (
        normalize_dosage_form(raw_item.get("dosage_form"), unit)
        if raw_item.get("dosage_form") or unit
        else None
    )
    route = normalize_route(raw_item.get("route")) if raw_item.get("route") else None

    dose_amount: float | None = None
    if raw_item.get("dose_amount") is not None and str(raw_item.get("dose_amount")).strip() != "":
        try:
            dose_amount = float(raw_item["dose_amount"])
        except (ValueError, TypeError):
            dose_amount = None

    frequency_text = (raw_item.get("frequency_text") or "").strip() or None
    frequency_per_day = parse_frequency_per_day(
        raw_item.get("frequency_per_day"),
        frequency_text,
    )

    quantity: float = 0.0
    if raw_item.get("quantity") is not None and str(raw_item.get("quantity")).strip() != "":
        try:
            quantity = float(raw_item["quantity"])
        except (ValueError, TypeError):
            quantity = 0.0

    expiration_date = normalize_date(raw_item.get("expiration_date"))
    start_date = normalize_date(raw_item.get("start_date"))
    end_date = normalize_date(raw_item.get("end_date"))

    return {
        "row_index": row_index,
        "medication_name": raw_name,
        "active_ingredient": active_ingredient,
        "strength": strength,
        "dosage_form": dosage_form,
        "manufacturer": (raw_item.get("manufacturer") or "").strip() or None,
        "dose_amount": dose_amount,
        "dose_unit": dose_unit,
        "frequency_per_day": frequency_per_day,
        "frequency_text": frequency_text,
        "route": route,
        "instructions": (raw_item.get("instructions") or "").strip() or None,
        "quantity": quantity,
        "unit": unit,
        "expiration_date": expiration_date,
        "start_date": start_date,
        "end_date": end_date,
        "confidence": float(raw_item.get("confidence", 1.0)),
        "field_confidences": raw_item.get("field_confidences") or {},
    }

