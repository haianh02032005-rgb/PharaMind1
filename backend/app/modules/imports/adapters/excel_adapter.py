import csv
import io
import re
import xml.etree.ElementTree as ET
import zipfile
from typing import Any
from xml.sax.saxutils import escape

from backend.app.modules.imports.adapters.base import BaseImportAdapter
from backend.app.modules.imports.exceptions import (
    ImportTemplateColumnError,
    ImportUnsupportedFileError,
)

# All 26 standard columns from §7
TEMPLATE_COLUMNS: list[str] = [
    "member_name",
    "member_identifier",
    "prescription_title",
    "doctor_name",
    "facility_name",
    "issued_at",
    "start_date",
    "end_date",
    "medication_name",
    "active_ingredient",
    "strength",
    "dosage_form",
    "dose_amount",
    "dose_unit",
    "frequency_per_day",
    "frequency_text",
    "route",
    "instructions",
    "quantity",
    "unit",
    "expiration_date",
    "schedule_times",
    "recurrence_type",
    "diagnosis_notes",
    "allergy_notes",
    "adverse_reaction_notes",
]

REQUIRED_COLUMNS: set[str] = {
    "medication_name",
    "dose_amount",
    "dose_unit",
}


def _col_letter(col_idx: int) -> str:
    """Convert 0-based column index to Excel column letters (A, B, ..., Z, AA)."""
    result = ""
    n = col_idx + 1
    while n > 0:
        n, rem = divmod(n - 1, 26)
        result = chr(65 + rem) + result
    return result


def _col_index_from_ref(cell_ref: str) -> int:
    """Convert Excel cell reference like 'AB12' to 0-based column index."""
    m = re.match(r"^([A-Z]+)", cell_ref.upper())
    if not m:
        return 0
    letters = m.group(1)
    idx = 0
    for ch in letters:
        idx = idx * 26 + (ord(ch) - 64)
    return idx - 1


def build_xlsx_bytes(headers: list[str], rows: list[list[Any]]) -> bytes:
    """Build a valid OOXML .xlsx workbook in memory using zipfile."""
    buf = io.BytesIO()
    all_rows = [headers] + rows

    sheet_rows_xml: list[str] = []
    for r_idx, row in enumerate(all_rows, start=1):
        cells_xml: list[str] = []
        for c_idx, val in enumerate(row):
            if val is None or str(val) == "":
                continue
            ref = f"{_col_letter(c_idx)}{r_idx}"
            text_val = escape(str(val))
            cells_xml.append(
                f'<c r="{ref}" t="inlineStr"><is><t>{text_val}</t></is></c>'
            )
        sheet_rows_xml.append(f'<row r="{r_idx}">{"".join(cells_xml)}</row>')

    worksheet_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<sheetData>{"".join(sheet_rows_xml)}</sheetData>'
        "</worksheet>"
    )

    content_types_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        "</Types>"
    )

    rels_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        "</Relationships>"
    )

    workbook_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<sheets><sheet name="PrescriptionImport" sheetId="1" r:id="rId1"/></sheets>'
        "</workbook>"
    )

    workbook_rels_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
        "</Relationships>"
    )

    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types_xml)
        zf.writestr("_rels/.rels", standalone_xml := rels_xml)
        zf.writestr("xl/workbook.xml", workbook_xml)
        zf.writestr("xl/_rels/workbook.xml.rels", workbook_rels_xml)
        zf.writestr("xl/worksheets/sheet1.xml", worksheet_xml)

    return buf.getvalue()


def generate_template_xlsx() -> bytes:
    """Generate the standard PHARMAMIND_PRESCRIPTION_IMPORT_TEMPLATE.xlsx file (§7)."""
    sample_rows = [
        [
            "Nguyễn Minh An",
            "MEM-001",
            "Đơn thuốc điều trị cảm cúm",
            "BS. Nguyễn Văn Hải",
            "Bệnh viện Đa khoa Tâm Anh",
            "2026-11-01",
            "2026-11-01",
            "2026-11-07",
            "Paracetamol 500mg",
            "Paracetamol",
            "500mg",
            "TABLET",
            "1",
            "tablet",
            "2",
            "2 lần/ngày sau ăn",
            "ORAL",
            "Uống sau ăn sáng và tối",
            "14",
            "tablet",
            "2028-06-30",
            "08:00,20:00",
            "DAILY",
            "Cảm cúm sốt nhẹ",
            "",
            "",
        ],
        [
            "Nguyễn Minh An",
            "MEM-001",
            "Đơn thuốc điều trị cảm cúm",
            "BS. Nguyễn Văn Hải",
            "Bệnh viện Đa khoa Tâm Anh",
            "2026-11-01",
            "2026-11-01",
            "2026-11-07",
            "Vitamin C 500mg",
            "Ascorbic Acid",
            "500mg",
            "TABLET",
            "1",
            "tablet",
            "1",
            "1 lần/ngày buổi sáng",
            "ORAL",
            "Uống sau ăn sáng",
            "7",
            "tablet",
            "2028-12-31",
            "08:00",
            "DAILY",
            "",
            "",
            "",
        ],
    ]
    return build_xlsx_bytes(TEMPLATE_COLUMNS, sample_rows)


class ExcelImportAdapter(BaseImportAdapter):
    parser_version = "excel-v1.0.0"

    def extract(
        self,
        file_bytes: bytes,
        filename: str,
        *,
        default_member_name: str | None = None,
    ) -> dict[str, Any]:
        ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
        if ext == "csv":
            rows = self._parse_csv_bytes(file_bytes)
        else:
            rows = self._parse_xlsx_bytes(file_bytes)

        if not rows:
            raise ImportTemplateColumnError("Tệp bảng tính trống hoặc không có dòng tiêu đề.")

        raw_headers = [str(h or "").strip().lower() for h in rows[0]]
        header_set = {h for h in raw_headers if h}

        missing = REQUIRED_COLUMNS - header_set
        has_freq = "frequency_per_day" in header_set or "frequency_text" in header_set
        if missing or not has_freq:
            missing_list = sorted(missing)
            if not has_freq:
                missing_list.append("frequency_per_day|frequency_text")
            raise ImportTemplateColumnError(
                f"Tệp nhập thiếu cột bắt buộc: {', '.join(missing_list)}"
            )

        data_dicts: list[dict[str, Any]] = []
        for row_vals in rows[1:]:
            if not any(str(v or "").strip() for v in row_vals):
                continue
            row_dict: dict[str, Any] = {}
            for idx, col_name in enumerate(raw_headers):
                if not col_name:
                    continue
                val = row_vals[idx] if idx < len(row_vals) else ""
                row_dict[col_name] = str(val).strip() if val is not None else ""
            data_dicts.append(row_dict)

        if not data_dicts:
            raise ImportTemplateColumnError("Tệp bảng tính không có dòng dữ liệu thuốc nào.")

        first = data_dicts[0]
        prescription_meta = {
            "member_name": first.get("member_name") or default_member_name,
            "member_identifier": first.get("member_identifier") or None,
            "prescription_title": first.get("prescription_title") or "Đơn thuốc nhập từ Excel",
            "doctor_name": first.get("doctor_name") or None,
            "facility_name": first.get("facility_name") or None,
            "issued_at": first.get("issued_at") or None,
            "start_date": first.get("start_date") or None,
            "end_date": first.get("end_date") or None,
            "diagnosis_notes": first.get("diagnosis_notes") or None,
            "allergy_notes": first.get("allergy_notes") or None,
            "adverse_reaction_notes": first.get("adverse_reaction_notes") or None,
            "field_confidences": {},
        }

        medications: list[dict[str, Any]] = []
        for row in data_dicts:
            row_copy = dict(row)
            row_copy["confidence"] = 1.0
            medications.append(row_copy)

        return {
            "headers": raw_headers,
            "overall_confidence": 1.0,
            "prescription_meta": prescription_meta,
            "medications": medications,
        }

    @staticmethod
    def _parse_csv_bytes(file_bytes: bytes) -> list[list[str]]:
        try:
            text = file_bytes.decode("utf-8-sig")
        except UnicodeDecodeError:
            raise ImportUnsupportedFileError("Không thể đọc định dạng mã hóa CSV (yêu cầu UTF-8).")
        reader = csv.reader(io.StringIO(text))
        return [list(r) for r in reader]

    @staticmethod
    def _parse_xlsx_bytes(file_bytes: bytes) -> list[list[str]]:
        try:
            zf = zipfile.ZipFile(io.BytesIO(file_bytes))
        except Exception as exc:
            raise ImportUnsupportedFileError("Tệp Excel (.xlsx) không hợp lệ hoặc bị hỏng.") from exc

        ns = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        shared_strings: list[str] = []

        if "xl/sharedStrings.xml" in zf.namelist():
            ss_root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
            for si in ss_root.findall("main:si", ns):
                texts = [t.text or "" for t in si.findall(".//main:t", ns)]
                shared_strings.append("".join(texts))

        sheet_name = next(
            (n for n in zf.namelist() if n.startswith("xl/worksheets/sheet") and n.endswith(".xml")),
            None,
        )
        if not sheet_name:
            raise ImportUnsupportedFileError("Không tìm thấy trang tính trong tệp Excel.")

        sheet_root = ET.fromstring(zf.read(sheet_name))
        parsed_rows: list[list[str]] = []

        for row_el in sheet_root.findall(".//main:sheetData/main:row", ns):
            row_cells: dict[int, str] = {}
            max_col = -1
            for c_el in row_el.findall("main:c", ns):
                ref = c_el.attrib.get("r", "")
                col_idx = _col_index_from_ref(ref) if ref else (max_col + 1)
                max_col = max(max_col, col_idx)
                c_type = c_el.attrib.get("t", "")

                cell_val = ""
                if c_type == "s":
                    v_el = c_el.find("main:v", ns)
                    if v_el is not None and v_el.text is not None:
                        s_idx = int(v_el.text)
                        if 0 <= s_idx < len(shared_strings):
                            cell_val = shared_strings[s_idx]
                elif c_type == "inlineStr":
                    t_els = c_el.findall(".//main:is//main:t", ns)
                    cell_val = "".join(t.text or "" for t in t_els)
                else:
                    v_el = c_el.find("main:v", ns)
                    if v_el is not None and v_el.text is not None:
                        cell_val = v_el.text

                row_cells[col_idx] = cell_val

            if max_col >= 0:
                row_list = [row_cells.get(i, "") for i in range(max_col + 1)]
                parsed_rows.append(row_list)

        return parsed_rows
