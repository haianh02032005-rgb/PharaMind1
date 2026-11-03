"""Advanced, deterministic quality benchmark for prescription OCR and Excel import.

This is a diagnostic benchmark rather than a CI pass/fail test. It compares hard
synthetic prescriptions with golden fields and prints a JSON report:

    python -m backend.tests.advanced_import_extraction_benchmark
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass
from datetime import date
from typing import Any

from backend.app.modules.imports.adapters.excel_adapter import (
    ExcelImportAdapter,
    build_xlsx_bytes,
)
from backend.app.modules.imports.adapters.ocr_adapter import OCRImportAdapter
from backend.app.modules.imports.exceptions import (
    ImportTemplateColumnError,
    ImportUnsupportedFileError,
)
from backend.app.modules.imports.parsers.medication_parser import parse_medication_item
from backend.app.modules.imports.parsers.prescription_parser import parse_prescription_meta
from backend.app.modules.imports.parsers.schedule_parser import parse_schedule_candidate


@dataclass
class Check:
    case: str
    field: str
    expected: Any
    actual: Any
    passed: bool


def _same(expected: Any, actual: Any) -> bool:
    if isinstance(expected, str) and isinstance(actual, str):
        return " ".join(expected.casefold().split()) == " ".join(actual.casefold().split())
    if isinstance(expected, float) and isinstance(actual, (float, int)):
        return abs(expected - float(actual)) < 1e-9
    return expected == actual


def _record(checks: list[Check], case: str, field: str, expected: Any, actual: Any) -> None:
    checks.append(Check(case, field, expected, actual, _same(expected, actual)))


def _normalize_extraction(extracted: dict[str, Any]) -> dict[str, Any]:
    meta = parse_prescription_meta(extracted.get("prescription_meta") or {})
    items: list[dict[str, Any]] = []
    for index, raw_item in enumerate(extracted.get("medications") or []):
        normalized = parse_medication_item(raw_item, index)
        normalized["schedule_times"] = parse_schedule_candidate(
            raw_item, normalized, meta
        )["schedule_times"]
        items.append(normalized)
    return {"meta": meta, "items": items}


def _check_expected(
    checks: list[Check], case: str, expected: dict[str, Any], actual: dict[str, Any]
) -> None:
    for field, value in expected.get("meta", {}).items():
        _record(checks, case, f"meta.{field}", value, actual["meta"].get(field))

    expected_items = expected.get("items", [])
    _record(checks, case, "item_count", len(expected_items), len(actual["items"]))
    for index, expected_item in enumerate(expected_items):
        actual_item = actual["items"][index] if index < len(actual["items"]) else {}
        for field, value in expected_item.items():
            _record(checks, case, f"items[{index}].{field}", value, actual_item.get(field))


def _run_ocr_benchmark(checks: list[Check], capabilities: dict[str, Any]) -> None:
    adapter = OCRImportAdapter()

    complex_text = """PHÒNG KHÁM ĐA KHOA AN TÂM
Họ tên: Nguyễn Thị Minh-Anh
Bác sĩ: BS.CKI Trần Hoàng Vũ
Chẩn đoán: Viêm phế quản co thắt / tăng huyết áp
Ngày kê: 01/11/2026
Điều trị từ 01/11/2026 đến 07/11/2026
1. Augmentin 625 mg - Uống 1 viên/lần, ngày 2 lần lúc 07:30 và 19:30 - SL: 14 viên
2. Prednisolon 5mg - Uống 0.5 viên buổi sáng 07:30 sau ăn - SL: 4 viên
3. Ventolin 100mcg - Xịt 2 nhát khi khó thở, tối đa 4 lần/ngày - SL: 01 bình
4. Tobradex - Nhỏ mắt phải 1 giọt/lần, 3 lần/ngày lúc 07:00; 13:00; 19:00 - SL: 01 lọ
"""
    complex_expected = {
        "meta": {
            "member_name": "Nguyễn Thị Minh-Anh",
            "doctor_name": "BS.CKI Trần Hoàng Vũ",
            "facility_name": "PHÒNG KHÁM ĐA KHOA AN TÂM",
            "diagnosis_notes": "Viêm phế quản co thắt / tăng huyết áp",
            "issued_at": "2026-11-01",
            "start_date": "2026-11-01",
            "end_date": "2026-11-07",
        },
        "items": [
            {
                "medication_name": "Augmentin 625 mg",
                "strength": "625mg",
                "dose_amount": 1.0,
                "dose_unit": "tablet",
                "frequency_per_day": 2.0,
                "route": "ORAL",
                "quantity": 14.0,
                "schedule_times": ["07:30", "19:30"],
            },
            {
                "medication_name": "Prednisolon 5mg",
                "strength": "5mg",
                "dose_amount": 0.5,
                "dose_unit": "tablet",
                "frequency_per_day": 1.0,
                "route": "ORAL",
                "quantity": 4.0,
                "schedule_times": ["07:30"],
            },
            {
                "medication_name": "Ventolin 100mcg",
                "strength": "100mcg",
                "dose_amount": 2.0,
                "dose_unit": "puff",
                "frequency_per_day": 4.0,
                "route": "INHALATION",
                "quantity": 1.0,
                "schedule_times": [],
            },
            {
                "medication_name": "Tobradex",
                "strength": None,
                "dose_amount": 1.0,
                "dose_unit": "drop",
                "frequency_per_day": 3.0,
                "route": "EYE",
                "quantity": 1.0,
                "schedule_times": ["07:00", "13:00", "19:00"],
            },
        ],
    }
    complex_actual = _normalize_extraction(
        adapter.extract(
            complex_text.encode("utf-8"),
            "don_thuoc_nhieu_dong_low.png",
            default_member_name="Nguyễn Thị Minh-Anh",
        )
    )
    _check_expected(checks, "ocr_complex_searchable_text", complex_expected, complex_actual)

    noisy_text = """DON THUOC NGOAI TRU
H0 TEN BN: LE THI THUY NGA
BS DIEU TRI: NGUYEN VAN HAI
CD: Dai thao duong type 2
I) Metf0rmin 500mg sang 1v, toi 1v
II) Gliclazide MR 30mg sang 1v truoc an
"""
    noisy_expected = {
        "meta": {
            "member_name": "LÊ THỊ THÚY NGA",
            "doctor_name": "NGUYỄN VĂN HẢI",
            "diagnosis_notes": "Đái tháo đường type 2",
        },
        "items": [
            {"medication_name": "Metformin 500mg", "frequency_per_day": 2.0},
            {"medication_name": "Gliclazide MR 30mg", "frequency_per_day": 1.0},
        ],
    }
    noisy_actual = _normalize_extraction(
        adapter.extract(
            noisy_text.encode("utf-8"),
            "scan_noise_low.jpg",
            default_member_name="LÊ THỊ THÚY NGA",
        )
    )
    _check_expected(checks, "ocr_noisy_text_and_roman_bullets", noisy_expected, noisy_actual)

    # A real binary image must be sent to an OCR engine. The current adapter is
    # expected to reject it; this exposes extraction coverage without hallucinating.
    one_pixel_png = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
    )
    try:
        adapter.extract(one_pixel_png, "real_scan.png")
        capabilities["real_image_ocr"] = "unexpectedly accepted"
    except ImportUnsupportedFileError:
        capabilities["unreadable_image"] = "rejected safely"
        capabilities["real_image_ocr"] = "covered by test_ocr_real_pipeline.py"

    # Readable prescription-like text with no recognized numbered item must not
    # silently create a medicine. This check detects fallback hallucination.
    incomplete_text = "ĐƠN THUỐC\nBệnh nhân: Trần An\nGhi chú: ảnh mất phần danh sách thuốc\n"
    try:
        incomplete = adapter.extract(incomplete_text.encode("utf-8"), "cropped.png")
        names = [item.get("medication_name") for item in incomplete.get("medications", [])]
    except ImportUnsupportedFileError:
        names = []
    _record(checks, "ocr_cropped_document_safety", "invented_medication_count", 0, len(names))
    capabilities["cropped_document_medications"] = names


def _excel_row(**overrides: Any) -> dict[str, Any]:
    row = {
        "member_name": "Phạm Gia Bảo",
        "member_identifier": "BN-0097",
        "prescription_title": "Đơn thuốc tim mạch và hen",
        "doctor_name": "BS. Nguyễn Hoàng An",
        "facility_name": "Bệnh viện Đa khoa Trung tâm",
        "issued_at": "2026-11-01",
        "start_date": "2026-11-01",
        "end_date": "2026-11-30",
        "medication_name": "Bisoprolol 2.5mg",
        "active_ingredient": "Bisoprolol",
        "strength": "2.5mg",
        "dosage_form": "TABLET",
        "dose_amount": "0.5",
        "dose_unit": "viên",
        "frequency_per_day": "1",
        "frequency_text": "1 lần/ngày",
        "route": "uống",
        "instructions": "Uống 0.5 viên lúc 06:45; theo dõi mạch",
        "quantity": "15",
        "unit": "viên",
        "expiration_date": "2028-12-31",
        "schedule_times": "06:45",
        "recurrence_type": "DAILY",
        "diagnosis_notes": "Tăng huyết áp; hen phế quản",
        "allergy_notes": "Penicillin",
        "adverse_reaction_notes": "Aspirin: khó thở",
    }
    row.update(overrides)
    return row


def _xlsx_from_dicts(headers: list[str], rows: list[dict[str, Any]]) -> bytes:
    return build_xlsx_bytes(headers, [[row.get(header, "") for header in headers] for row in rows])


def _run_excel_benchmark(checks: list[Check], capabilities: dict[str, Any]) -> None:
    adapter = ExcelImportAdapter()
    headers = [
        "member_name", "member_identifier", "prescription_title", "doctor_name",
        "facility_name", "issued_at", "start_date", "end_date", "medication_name",
        "active_ingredient", "strength", "dosage_form", "dose_amount", "dose_unit",
        "frequency_per_day", "frequency_text", "route", "instructions", "quantity",
        "unit", "expiration_date", "schedule_times", "recurrence_type",
        "diagnosis_notes", "allergy_notes", "adverse_reaction_notes",
    ]
    rows = [
        _excel_row(),
        _excel_row(
            medication_name="Ventolin Evohaler 100mcg",
            active_ingredient="Salbutamol",
            strength="100mcg",
            dosage_form="INHALER",
            dose_amount="2",
            dose_unit="nhát xịt",
            frequency_per_day="",
            frequency_text="khi khó thở",
            route="xịt",
            instructions="Xịt 2 nhát khi khó thở; tối đa 4 lần/ngày",
            quantity="1",
            unit="unit",
            schedule_times="",
            recurrence_type="AS_NEEDED",
        ),
        _excel_row(
            medication_name="Insulin glargine 100 IU/mL",
            active_ingredient="Insulin glargine",
            strength="100 IU/mL",
            dosage_form="INJECTION",
            dose_amount="12",
            dose_unit="unit",
            frequency_per_day="1",
            frequency_text="mỗi tối",
            route="tiêm",
            instructions="Tiêm dưới da lúc 21:15",
            quantity="3",
            unit="unit",
            schedule_times="21:15",
        ),
    ]
    difficult_xlsx = _xlsx_from_dicts(headers, rows)
    actual = _normalize_extraction(adapter.extract(difficult_xlsx, "advanced.xlsx"))
    expected = {
        "meta": {
            "member_name": "Phạm Gia Bảo",
            "member_identifier": "BN-0097",
            "doctor_name": "BS. Nguyễn Hoàng An",
            "facility_name": "Bệnh viện Đa khoa Trung tâm",
            "issued_at": "2026-11-01",
            "start_date": "2026-11-01",
            "end_date": "2026-11-30",
            "diagnosis_notes": "Tăng huyết áp; hen phế quản",
            "allergy_notes": "Penicillin",
            "adverse_reaction_notes": "Aspirin: khó thở",
        },
        "items": [
            {
                "medication_name": "Bisoprolol 2.5mg", "strength": "2.5mg",
                "dose_amount": 0.5, "dose_unit": "tablet", "frequency_per_day": 1.0,
                "route": "ORAL", "quantity": 15.0, "schedule_times": ["06:45"],
            },
            {
                "medication_name": "Ventolin Evohaler 100mcg", "strength": "100mcg",
                "dose_amount": 2.0, "dose_unit": "puff", "frequency_per_day": None,
                "route": "INHALATION", "quantity": 1.0, "schedule_times": [],
            },
            {
                "medication_name": "Insulin glargine 100 IU/mL", "strength": "100 IU/mL",
                "dose_amount": 12.0, "dose_unit": "unit", "frequency_per_day": 1.0,
                "route": "INJECTION", "quantity": 3.0, "schedule_times": ["21:15"],
            },
        ],
    }
    _check_expected(checks, "excel_complex_xlsx", expected, actual)

    shuffled_headers = [
        " schedule_times ", "FREQUENCY_TEXT", "dose_unit", "medication_name",
        "quantity", "dose_amount", "route", "member_name",
    ]
    shuffled_values = [["08:00|20:00", "sáng và tối", "viên", "Metformin XR 500mg", "60", "1", "uống", "Võ Thu Hà"]]
    shuffled = build_xlsx_bytes(shuffled_headers, shuffled_values)
    shuffled_actual = _normalize_extraction(adapter.extract(shuffled, "shuffled.xlsx"))
    _check_expected(
        checks,
        "excel_shuffled_case_and_sparse_columns",
        {
            "meta": {"member_name": "Võ Thu Hà"},
            "items": [{
                "medication_name": "Metformin XR 500mg", "dose_amount": 1.0,
                "dose_unit": "tablet", "frequency_per_day": 2.0,
                "route": "ORAL", "quantity": 60.0,
                "schedule_times": ["08:00", "20:00"],
            }],
        },
        shuffled_actual,
    )

    csv_bytes = (
        '\ufeffmember_name,medication_name,dose_amount,dose_unit,frequency_text,instructions\r\n'
        '"Đỗ, Minh Châu","Kali chlorid 600mg",1,viên,"2 lần/ngày","Uống sau ăn, không nhai"\r\n'
    ).encode("utf-8")
    quoted_actual = _normalize_extraction(adapter.extract(csv_bytes, "quoted.csv"))
    _check_expected(
        checks,
        "excel_csv_bom_quoted_commas",
        {
            "meta": {"member_name": "Đỗ, Minh Châu"},
            "items": [{
                "medication_name": "Kali chlorid 600mg", "dose_amount": 1.0,
                "frequency_per_day": 2.0, "instructions": "Uống sau ăn, không nhai",
            }],
        },
        quoted_actual,
    )

    # Excel stores dates as serial numbers when cells are date-formatted. The
    # lightweight parser currently sees the raw serial without evaluating style.
    serial = str((date(2026, 11, 1) - date(1899, 12, 30)).days)
    serial_row = _excel_row(issued_at=serial, start_date=serial, end_date=str(int(serial) + 7))
    serial_actual = _normalize_extraction(adapter.extract(_xlsx_from_dicts(headers, [serial_row]), "native_dates.xlsx"))
    _check_expected(
        checks,
        "excel_native_date_serials",
        {"meta": {"issued_at": "2026-11-01", "start_date": "2026-11-01", "end_date": "2026-11-08"}, "items": [
            {"medication_name": "Bisoprolol 2.5mg"}
        ]},
        serial_actual,
    )

    semicolon_csv = (
        "medication_name;dose_amount;dose_unit;frequency_per_day\n"
        "Paracetamol 500mg;1;viên;3\n"
    ).encode("utf-8")
    try:
        adapter.extract(semicolon_csv, "regional.csv")
        capabilities["semicolon_csv"] = "accepted"
    except ImportTemplateColumnError:
        capabilities["semicolon_csv"] = "unsupported"

    repeated_header_rows = [rows[0], dict(zip(headers, headers)), rows[1]]
    repeated = adapter.extract(_xlsx_from_dicts(headers, repeated_header_rows), "repeated_header.xlsx")
    _record(
        checks,
        "excel_repeated_header_safety",
        "item_count",
        2,
        len(repeated.get("medications", [])),
    )

    try:
        adapter.extract(
            build_xlsx_bytes(
                ["medication_name", "dose_unit", "frequency_per_day"],
                [["Paracetamol 500mg", "viên", "3"]],
            ),
            "missing_required.xlsx",
        )
        capabilities["missing_required_columns"] = "incorrectly accepted"
    except ImportTemplateColumnError:
        capabilities["missing_required_columns"] = "rejected correctly"

    try:
        adapter.extract(b"not-a-zip", "corrupt.xlsx")
        capabilities["corrupt_xlsx"] = "incorrectly accepted"
    except ImportUnsupportedFileError:
        capabilities["corrupt_xlsx"] = "rejected correctly"


def _summary(checks: list[Check], prefix: str) -> dict[str, Any]:
    selected = [check for check in checks if check.case.startswith(prefix)]
    passed = sum(check.passed for check in selected)
    total = len(selected)
    return {
        "passed_fields": passed,
        "total_fields": total,
        "exact_accuracy_percent": round((passed / total * 100) if total else 0.0, 2),
    }


def _case_summaries(checks: list[Check]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for case_name in sorted({check.case for check in checks}):
        selected = [check for check in checks if check.case == case_name]
        passed = sum(check.passed for check in selected)
        result[case_name] = {
            "passed_fields": passed,
            "total_fields": len(selected),
            "exact_accuracy_percent": round(passed / len(selected) * 100, 2),
        }
    return result


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    checks: list[Check] = []
    capabilities: dict[str, Any] = {}
    _run_ocr_benchmark(checks, capabilities)
    _run_excel_benchmark(checks, capabilities)

    failures = [asdict(check) for check in checks if not check.passed]
    report = {
        "benchmark": "advanced synthetic prescription extraction",
        "scoring": "exact field match after adapter + current normalization pipeline",
        "summary": {
            "ocr": _summary(checks, "ocr_"),
            "excel": _summary(checks, "excel_"),
            "overall": {
                "passed_fields": sum(check.passed for check in checks),
                "total_fields": len(checks),
                "exact_accuracy_percent": round(
                    sum(check.passed for check in checks) / len(checks) * 100, 2
                ),
            },
        },
        "cases": _case_summaries(checks),
        "capabilities": capabilities,
        "failed_checks": failures,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
