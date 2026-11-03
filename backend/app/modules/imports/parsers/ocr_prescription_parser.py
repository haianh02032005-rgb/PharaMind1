"""Conservative deterministic parser for Vietnamese prescription OCR text."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Any

from backend.app.modules.imports.normalizers.date_normalizer import normalize_date
from backend.app.modules.imports.normalizers.dosage_normalizer import (
    parse_frequency_per_day,
)


DATE_TOKEN = re.compile(
    r"\b(?:\d{4}[./-]\d{1,2}[./-]\d{1,2}|\d{1,2}[./-]\d{1,2}[./-]\d{4})\b"
)
ITEM_MARKER = re.compile(
    r"^\s*(?:(?:\d{1,3}|[ivxlcdm]{1,7})[.)]|[•●▪*-])\s+",
    re.IGNORECASE,
)
TIME_TOKEN = re.compile(r"\b(?:[01]?\d|2[0-3]):[0-5]\d\b")
STRENGTH_TOKEN = re.compile(
    r"\b\d+(?:[.,]\d+)?\s*(?:mg|mcg|µg|g|iu(?:\s*/\s*ml)?|ui(?:\s*/\s*ml)?|%|ml)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ParsedOCRPrescription:
    prescription_meta: dict[str, Any]
    medications: list[dict[str, Any]]


def _fold(value: str) -> str:
    value = value.replace("đ", "d").replace("Đ", "D")
    value = "".join(
        char for char in unicodedata.normalize("NFD", value) if not unicodedata.combining(char)
    )
    return re.sub(r"\s+", " ", value.casefold()).strip()


def _after_separator(line: str) -> str | None:
    parts = re.split(r"\s*[:=]\s*", line, maxsplit=1)
    if len(parts) == 2 and parts[1].strip():
        return parts[1].strip()
    return None


def _matches_label(folded: str, labels: tuple[str, ...]) -> bool:
    return any(
        folded == label
        or folded.startswith(label + ":")
        or folded.startswith(label + " =")
        or (folded.startswith(label + " ") and (":" in folded or "=" in folded))
        for label in labels
    )


def _extract_dates(line: str) -> list[str]:
    result: list[str] = []
    for token in DATE_TOKEN.findall(line):
        normalized = normalize_date(token)
        if normalized and normalized not in result:
            result.append(normalized)
    return result


def _collect_medication_lines(lines: list[str]) -> list[str]:
    medications: list[str] = []
    current: list[str] = []
    for line in lines:
        marker = ITEM_MARKER.match(line)
        if marker:
            if current:
                medications.append(" ".join(current).strip())
            current = [line[marker.end() :].strip()]
            continue
        if current:
            folded = _fold(line)
            if _is_header_or_footer(folded):
                medications.append(" ".join(current).strip())
                current = []
            elif line.strip():
                current.append(line.strip())
    if current:
        medications.append(" ".join(current).strip())
    return [line for line in medications if line]


def _is_header_or_footer(folded: str) -> bool:
    prefixes = (
        "ho ten", "h0 ten", "benh nhan", "nguoi benh", "patient",
        "bac si", "bs dieu tri", "doctor", "chan doan", "cd:",
        "di ung", "phan ung", "ngay ke", "ngay cap", "ngay bat dau",
        "ngay ket thuc", "dieu tri tu", "loi dan", "tai kham", "ky ten",
    )
    return any(folded.startswith(prefix) for prefix in prefixes)


def _canonical_dose_unit(raw_unit: str) -> str | None:
    folded = _fold(raw_unit).replace(".", "")
    if folded in {"vien", "v", "tablet", "tab"}:
        return "tablet"
    if folded in {"vien nang", "capsule", "cap"}:
        return "capsule"
    if folded in {"ml", "milliliter"}:
        return "ml"
    if folded in {"mg", "milligram"}:
        return "mg"
    if folded in {"giot", "drop"}:
        return "drop"
    if folded in {"nhat", "nhat xit", "puff"}:
        return "puff"
    if folded in {"don vi", "dv", "unit", "iu", "ui"}:
        return "unit"
    if folded in {"goi", "ong", "lo", "binh", "tuyp"}:
        return "unit"
    return None


def _parse_amount_and_unit(text: str) -> tuple[float | None, str | None]:
    patterns = (
        r"(?:uong|dung|ngam|xit|nho|tiem|boi)\s+(?:\w+\s+){0,4}?(\d+(?:[.,]\d+)?)\s*(vien nang|vien|v\b|ml\b|mg\b|giot|nhat xit|nhat|don vi|dv\b|unit\b|iu\b|ui\b)",
        r"(\d+(?:[.,]\d+)?)\s*(vien nang|vien|v\b|ml\b|mg\b|giot|nhat xit|nhat|don vi|dv\b|unit\b|iu\b|ui\b)\s*(?:/\s*lan|moi lan)",
        r"(?:sang|trua|chieu|toi)\s+(\d+(?:[.,]\d+)?)\s*(v\b|vien|ml\b|giot|nhat|don vi|unit\b)",
    )
    folded = _fold(text)
    for pattern in patterns:
        match = re.search(pattern, folded, re.IGNORECASE)
        if not match:
            continue
        try:
            amount = float(match.group(1).replace(",", "."))
        except ValueError:
            continue
        return amount, _canonical_dose_unit(match.group(2))
    return None, None


def _parse_route(text: str) -> str | None:
    folded = _fold(text)
    if "nho mat" in folded:
        return "EYE"
    if "nho tai" in folded:
        return "EAR"
    if "xit mui" in folded or "nho mui" in folded:
        return "NASAL"
    if "xit" in folded or "hit" in folded:
        return "INHALATION"
    if "tiem" in folded:
        return "INJECTION"
    if "boi" in folded or "ngoai da" in folded:
        return "TOPICAL"
    if "uong" in folded or "ngam" in folded:
        return "ORAL"
    return None


def _parse_quantity(text: str) -> tuple[float, str | None]:
    folded = _fold(text)
    match = re.search(
        r"(?:\bsl\b|so luong)\s*[:=]?\s*(\d+(?:[.,]\d+)?)\s*(vien|v\b|goi|ong|lo|binh|tuyp|ml\b|unit\b|don vi)?",
        folded,
    )
    if not match:
        return 0.0, None
    try:
        quantity = float(match.group(1).replace(",", "."))
    except ValueError:
        return 0.0, None
    return quantity, _canonical_dose_unit(match.group(2) or "") or "unit"


def _parse_frequency(text: str) -> tuple[float | None, str, str]:
    folded = _fold(text)
    recurrence_type = "AS_NEEDED" if any(token in folded for token in ("khi can", "khi dau", "khi kho tho", "neu can", "prn")) else "DAILY"
    patterns = (
        r"(?:toi da\s*)?(\d+(?:[.,]\d+)?)\s*lan\s*/?\s*(?:ngay|24\s*h)",
        r"(?:ngay|moi ngay)\s*(\d+(?:[.,]\d+)?)\s*lan",
    )
    for pattern in patterns:
        match = re.search(pattern, folded)
        if match:
            return float(match.group(1).replace(",", ".")), text, recurrence_type
    return parse_frequency_per_day(None, text), text, recurrence_type


def _extract_medication_name(text: str) -> str:
    first_segment = re.split(r"\s+[-–—]\s+", text, maxsplit=1)[0].strip(" ;,")
    if first_segment != text.strip(" ;,"):
        return first_segment

    strength = STRENGTH_TOKEN.search(text)
    if strength:
        return text[: strength.end()].strip(" ;,")
    cut = re.search(
        r"\s+(?:uong|uống|xit|xịt|nho|nhỏ|tiem|tiêm|boi|bôi|sang|sáng|toi|tối)\b",
        text,
        re.IGNORECASE,
    )
    return (text[: cut.start()] if cut else text).strip(" ;,")


def _parse_medication(text: str, confidence: float) -> dict[str, Any]:
    name = _extract_medication_name(text)
    dose_amount, dose_unit = _parse_amount_and_unit(text)
    route = _parse_route(text)
    frequency_per_day, frequency_text, recurrence_type = _parse_frequency(text)
    quantity, quantity_unit = _parse_quantity(text)
    schedule_times = sorted(set(TIME_TOKEN.findall(text)))

    completeness = sum(
        value is not None and value != ""
        for value in (name, dose_amount, dose_unit, frequency_per_day or frequency_text, route)
    ) / 5
    item_confidence = round(max(0.0, min(1.0, confidence * (0.55 + 0.45 * completeness))), 4)
    field_confidences = {
        "medication_name": confidence,
        "dose_amount": item_confidence if dose_amount is not None else 0.0,
        "dose_unit": item_confidence if dose_unit is not None else 0.0,
        "frequency_per_day": item_confidence if frequency_per_day is not None else 0.0,
        "route": item_confidence if route is not None else 0.0,
        "quantity": item_confidence if quantity > 0 else 0.0,
    }
    return {
        "medication_name": name,
        "dose_amount": dose_amount,
        "dose_unit": dose_unit,
        "frequency_per_day": frequency_per_day,
        "frequency_text": frequency_text,
        "route": route,
        "instructions": text,
        "quantity": quantity,
        "unit": quantity_unit or dose_unit,
        "schedule_times": schedule_times,
        "recurrence_type": recurrence_type,
        "confidence": item_confidence,
        "field_confidences": field_confidences,
    }


def parse_ocr_prescription(
    text: str,
    *,
    default_member_name: str | None,
    confidence: float,
) -> ParsedOCRPrescription:
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines() if line.strip()]
    member_name: str | None = None
    doctor_name: str | None = None
    facility_name: str | None = None
    diagnosis_notes: str | None = None
    allergy_notes: str | None = None
    adverse_reaction_notes: str | None = None
    issued_at: str | None = None
    start_date: str | None = None
    end_date: str | None = None

    for line in lines:
        folded = _fold(line)
        value = _after_separator(line)
        if _matches_label(folded, ("ho ten", "h0 ten", "ho va ten", "benh nhan", "benh nhan", "nguoi benh", "patient")):
            member_name = value or member_name
        elif _matches_label(folded, ("bac si", "bs", "bs dieu tri", "bac si dieu tri", "doctor")):
            doctor_name = value or doctor_name
        elif folded.startswith(("benh vien", "phong kham", "co so y te", "facility")):
            facility_name = value or line
        elif _matches_label(folded, ("chan doan", "cd", "diagnosis")):
            diagnosis_notes = value or diagnosis_notes
        elif _matches_label(folded, ("di ung", "allergy")):
            allergy_notes = value or allergy_notes
        elif _matches_label(folded, ("phan ung", "phan ung thuoc", "adverse")):
            adverse_reaction_notes = value or adverse_reaction_notes

        dates = _extract_dates(line)
        if dates:
            if any(token in folded for token in ("ngay ke", "ngay cap", "issued", "ke don ngay")):
                issued_at = dates[0]
            if any(token in folded for token in ("ngay bat dau", "bat dau", "dieu tri tu")):
                start_date = dates[0]
            if any(token in folded for token in ("ngay ket thuc", "ket thuc", "den ngay")):
                end_date = dates[-1]
            if " tu " in f" {folded} " and " den " in f" {folded} " and len(dates) >= 2:
                start_date, end_date = dates[0], dates[-1]

    medications = [
        _parse_medication(line, confidence)
        for line in _collect_medication_lines(lines)
    ]
    member_from_document = member_name is not None
    if member_name is None:
        member_name = default_member_name

    field_confidences = {
        "member_name": confidence if member_from_document else 0.0,
        "doctor_name": confidence if doctor_name else 0.0,
        "facility_name": confidence if facility_name else 0.0,
        "issued_at": confidence if issued_at else 0.0,
        "start_date": confidence if start_date else 0.0,
        "end_date": confidence if end_date else 0.0,
    }
    title = f"Đơn thuốc - {diagnosis_notes}" if diagnosis_notes else "Đơn thuốc OCR"
    return ParsedOCRPrescription(
        prescription_meta={
            "member_name": member_name,
            "prescription_title": title,
            "doctor_name": doctor_name,
            "facility_name": facility_name,
            "issued_at": issued_at,
            "start_date": start_date,
            "end_date": end_date,
            "diagnosis_notes": diagnosis_notes,
            "allergy_notes": allergy_notes,
            "adverse_reaction_notes": adverse_reaction_notes,
            "field_confidences": field_confidences,
        },
        medications=medications,
    )
