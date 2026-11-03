from __future__ import annotations

import shutil
from io import BytesIO
from pathlib import Path

import pytest

from backend.app.core.config import PROJECT_ROOT, settings
from backend.app.modules.imports.adapters.ocr_adapter import OCRImportAdapter
from backend.app.modules.imports.parsers.medication_parser import parse_medication_item
from backend.app.modules.imports.parsers.prescription_parser import parse_prescription_meta
from backend.app.modules.imports.parsers.schedule_parser import parse_schedule_candidate


COMPLEX_PRESCRIPTION_TEXT = """PHÒNG KHÁM ĐA KHOA AN TÂM
Họ tên: Nguyễn Thị Minh-Anh
Bác sĩ: BS.CKI Trần Hoàng Vũ
Chẩn đoán: Viêm phế quản co thắt
Ngày kê: 01/11/2026
Điều trị từ 01/11/2026 đến 07/11/2026
1. Augmentin 625 mg - Uống 1 viên/lần, ngày 2 lần lúc 07:30 và 19:30 - SL: 14 viên
2. Prednisolon 5mg - Uống 0.5 viên buổi sáng 07:30 sau ăn - SL: 4 viên
3. Ventolin 100mcg - Xịt 2 nhát khi khó thở, tối đa 4 lần/ngày - SL: 1 bình
4. Tobradex - Nhỏ mắt phải 1 giọt/lần, 3 lần/ngày lúc 07:00; 13:00; 19:00 - SL: 1 lọ
"""


def _normalized(text: str):
    extracted = OCRImportAdapter().extract(
        text.encode("utf-8"), "searchable-prescription.txt", default_member_name="Nguyễn Thị Minh-Anh"
    )
    meta = parse_prescription_meta(extracted["prescription_meta"])
    items = []
    for index, raw_item in enumerate(extracted["medications"]):
        item = parse_medication_item(raw_item, index)
        item["schedule_times"] = parse_schedule_candidate(raw_item, item, meta)["schedule_times"]
        items.append(item)
    return meta, items


def test_complex_vietnamese_prescription_text_is_parsed_conservatively():
    meta, items = _normalized(COMPLEX_PRESCRIPTION_TEXT)

    assert meta["member_name"] == "Nguyễn Thị Minh-Anh"
    assert meta["doctor_name"] == "BS.CKI Trần Hoàng Vũ"
    assert meta["issued_at"] == "2026-11-01"
    assert meta["start_date"] == "2026-11-01"
    assert meta["end_date"] == "2026-11-07"
    assert len(items) == 4

    assert items[0]["dose_amount"] == 1.0
    assert items[0]["frequency_per_day"] == 2.0
    assert items[0]["quantity"] == 14.0
    assert items[0]["schedule_times"] == ["07:30", "19:30"]

    assert items[1]["dose_amount"] == 0.5
    assert items[2]["dose_unit"] == "puff"
    assert items[2]["route"] == "INHALATION"
    assert items[3]["dose_unit"] == "drop"
    assert items[3]["route"] == "EYE"


def test_cropped_prescription_never_invents_a_medication():
    extracted = OCRImportAdapter().extract(
        "ĐƠN THUỐC\nBệnh nhân: Trần An\nGhi chú: ảnh mất phần danh sách thuốc".encode("utf-8"),
        "cropped.txt",
        default_member_name="Trần An",
    )
    assert extracted["medications"] == []


def _windows_tesseract() -> Path | None:
    discovered = shutil.which("tesseract")
    if discovered:
        return Path(discovered)
    candidate = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
    return candidate if candidate.is_file() else None


def _font_path() -> Path | None:
    candidates = [
        Path(r"C:\Windows\Fonts\arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    return next((path for path in candidates if path.is_file()), None)


def _make_prescription_png() -> bytes:
    from PIL import Image, ImageDraw, ImageFont

    font_path = _font_path()
    if not font_path:
        pytest.skip("No Unicode TrueType font is installed for the OCR integration test")
    title_font = ImageFont.truetype(str(font_path), 54)
    body_font = ImageFont.truetype(str(font_path), 34)
    image = Image.new("RGB", (2200, 2500), "white")
    draw = ImageDraw.Draw(image)
    draw.text((700, 80), "ĐƠN THUỐC", font=title_font, fill="black")
    lines = [
        "PHÒNG KHÁM ĐA KHOA AN TÂM",
        "Họ tên: Nguyễn Văn An",
        "Bác sĩ: Trần Hoàng Vũ",
        "Chẩn đoán: Viêm phế quản",
        "Ngày kê: 01/11/2026",
        "Điều trị từ 01/11/2026 đến 07/11/2026",
        "1. Paracetamol 500mg - Uống 1 viên/lần, ngày 3 lần",
        "   lúc 07:00; 13:00; 19:00 - SL: 15 viên",
        "2. Ventolin 100mcg - Xịt 2 nhát khi khó thở,",
        "   tối đa 4 lần/ngày - SL: 1 bình",
    ]
    y = 220
    for line in lines:
        draw.text((140, y), line, font=body_font, fill="black")
        y += 115
    output = BytesIO()
    image.save(output, format="PNG", dpi=(300, 300))
    return output.getvalue()


def _make_scanned_prescription_pdf() -> bytes:
    from PIL import Image

    image = Image.open(BytesIO(_make_prescription_png())).convert("RGB")
    output = BytesIO()
    image.save(output, format="PDF", resolution=300.0)
    return output.getvalue()


def test_real_tesseract_reads_a_synthetic_vietnamese_prescription_image():
    tesseract = _windows_tesseract()
    if not tesseract:
        pytest.skip("Tesseract binary is not installed")

    local_tessdata = PROJECT_ROOT / ".tessdata"
    if not (local_tessdata / "vie.traineddata").is_file():
        pytest.skip("Vietnamese Tesseract language data is not installed")

    previous_cmd = settings.ocr_tesseract_cmd
    previous_data = settings.ocr_tessdata_dir
    try:
        settings.ocr_tesseract_cmd = str(tesseract)
        settings.ocr_tessdata_dir = str(local_tessdata)
        result = OCRImportAdapter().extract(
            _make_prescription_png(),
            "synthetic_real_scan.png",
            default_member_name="Nguyễn Văn An",
        )
    finally:
        settings.ocr_tesseract_cmd = previous_cmd
        settings.ocr_tessdata_dir = previous_data

    assert result["ocr_engine"] == "tesseract-image"
    assert result["overall_confidence"] >= 0.70
    assert "Paracetamol" in result["raw_text"]
    assert "Ventolin" in result["raw_text"]
    assert len(result["medications"]) == 2
    assert result["medications"][0]["dose_amount"] == 1.0
    assert result["medications"][0]["frequency_per_day"] == 3.0
    assert result["medications"][1]["dose_unit"] == "puff"
    assert result["medications"][1]["route"] == "INHALATION"


def test_scanned_pdf_is_rendered_then_ocr_processed():
    tesseract = _windows_tesseract()
    if not tesseract:
        pytest.skip("Tesseract binary is not installed")
    if not settings.ocr_poppler_path and not shutil.which("pdftoppm"):
        pytest.skip("Poppler is not installed or OCR_POPPLER_PATH is not configured")

    local_tessdata = PROJECT_ROOT / ".tessdata"
    if not (local_tessdata / "vie.traineddata").is_file():
        pytest.skip("Vietnamese Tesseract language data is not installed")

    previous_cmd = settings.ocr_tesseract_cmd
    previous_data = settings.ocr_tessdata_dir
    try:
        settings.ocr_tesseract_cmd = str(tesseract)
        settings.ocr_tessdata_dir = str(local_tessdata)
        result = OCRImportAdapter().extract(
            _make_scanned_prescription_pdf(),
            "synthetic_scanned_prescription.pdf",
            default_member_name="Nguyễn Văn An",
        )
    finally:
        settings.ocr_tesseract_cmd = previous_cmd
        settings.ocr_tessdata_dir = previous_data

    assert result["ocr_engine"] == "pdf-text+tesseract"
    assert result["overall_confidence"] >= 0.70
    assert len(result["medications"]) == 2
    assert result["medications"][0]["medication_name"].startswith("Paracetamol")
    assert result["medications"][1]["medication_name"].startswith("Ventolin")
