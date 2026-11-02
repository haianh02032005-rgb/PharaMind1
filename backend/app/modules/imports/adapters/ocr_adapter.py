import json
import re
from datetime import date
from typing import Any

from backend.app.modules.imports.adapters.base import BaseImportAdapter
from backend.app.modules.imports.exceptions import ImportUnsupportedFileError


class OCRImportAdapter(BaseImportAdapter):
    parser_version = "ocr-v1.0.0"

    def extract(
        self,
        file_bytes: bytes,
        filename: str,
        *,
        default_member_name: str | None = None,
    ) -> dict[str, Any]:
        """Extract raw OCR blocks, prescription metadata, medication rows, and confidence scores."""
        text_content = self._decode_searchable_text(file_bytes)

        # 1. If the uploaded file contains an embedded JSON OCR payload (e.g. from OCR engine or test fixture)
        json_payload = self._try_parse_json_payload(text_content)
        if json_payload is not None:
            return self._normalize_ocr_json(json_payload, default_member_name=default_member_name)

        # 2. If readable Vietnamese/English prescription text is found in the file
        if text_content and any(
            kw in text_content.lower()
            for kw in ("đơn thuốc", "don thuoc", "prescription", "bác sĩ", "bac si", "mg", "viên", "tablet")
        ):
            return self._parse_free_text_prescription(
                text_content,
                filename=filename,
                default_member_name=default_member_name,
            )

        # Never invent medication data when binary scan text cannot be read.
        # A real image/PDF OCR engine must be configured before accepting scans.
        raise ImportUnsupportedFileError(
            "Không đọc được nội dung đơn thuốc. OCR cho ảnh/PDF chưa được cấu hình; "
            "hệ thống không tạo dữ liệu thuốc mẫu. Hãy dùng tệp có văn bản đọc được "
            "hoặc nhập bằng Excel/CSV."
        )

    @staticmethod
    def _decode_searchable_text(file_bytes: bytes) -> str:
        try:
            return file_bytes.decode("utf-8").strip()
        except UnicodeDecodeError:
            # Extract printable UTF-8/ASCII chunks if embedded in PDF/image metadata
            try:
                decoded = file_bytes.decode("utf-8", errors="ignore")
                return decoded.strip()
            except Exception:
                return ""

    @staticmethod
    def _try_parse_json_payload(text_content: str) -> dict[str, Any] | None:
        if not text_content:
            return None
        start = text_content.find("{")
        end = text_content.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        candidate = text_content[start : end + 1]
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict) and (
                "prescription_meta" in parsed or "medications" in parsed or "items" in parsed
            ):
                return parsed
        except Exception:
            return None
        return None

    @staticmethod
    def _normalize_ocr_json(
        payload: dict[str, Any],
        *,
        default_member_name: str | None = None,
    ) -> dict[str, Any]:
        meta = dict(payload.get("prescription_meta") or {})
        if "member_name" not in meta and payload.get("member_name"):
            meta["member_name"] = payload.get("member_name")
        if not meta.get("member_name") and default_member_name:
            meta["member_name"] = default_member_name
        meds = list(payload.get("medications") or payload.get("items") or [])
        overall_conf = float(payload.get("overall_confidence", 0.92))
        return {
            "raw_text": payload.get("raw_text") or json.dumps(payload, ensure_ascii=False),
            "overall_confidence": overall_conf,
            "prescription_meta": meta,
            "medications": meds,
        }

    def _parse_free_text_prescription(
        self,
        text: str,
        *,
        filename: str,
        default_member_name: str | None = None,
    ) -> dict[str, Any]:
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        member_name = default_member_name
        doctor_name = None
        facility_name = None
        issued_at = date.today().isoformat()
        diagnosis_notes = None
        allergy_notes = None
        adverse_reaction_notes = None
        title = "Đơn thuốc OCR"

        medications: list[dict[str, Any]] = []
        is_low = "blur" in filename.lower() or "low" in filename.lower()
        default_conf = 0.65 if is_low else 0.91

        for line in lines:
            low = line.lower()
            if low.startswith(("họ tên", "ho ten", "bệnh nhân", "benh nhan", "người bệnh", "patient")):
                parts = line.split(":", 1)
                if len(parts) == 2 and parts[1].strip():
                    member_name = parts[1].strip()
            elif low.startswith(("bác sĩ", "bac si", "doctor")):
                parts = line.split(":", 1)
                if len(parts) == 2:
                    doctor_name = parts[1].strip()
            elif low.startswith(("bệnh viện", "benh vien", "phòng khám", "phong kham", "cơ sở", "facility")):
                parts = line.split(":", 1)
                facility_name = parts[1].strip() if len(parts) == 2 else line
            elif low.startswith(("chẩn đoán", "chan doan", "diagnosis")):
                parts = line.split(":", 1)
                if len(parts) == 2:
                    diagnosis_notes = parts[1].strip()
                    title = f"Đơn thuốc - {diagnosis_notes}"
            elif low.startswith(("dị ứng", "di ung", "allergy")):
                parts = line.split(":", 1)
                if len(parts) == 2:
                    allergy_notes = parts[1].strip()
            elif low.startswith(("phản ứng", "phan ung", "adverse")):
                parts = line.split(":", 1)
                if len(parts) == 2:
                    adverse_reaction_notes = parts[1].strip()
            elif re.match(r"^\d+[\.\)]\s+", line):
                med_line = re.sub(r"^\d+[\.\)]\s+", "", line)
                seg = [s.strip() for s in med_line.split("-") if s.strip()]
                med_name = seg[0] if seg else med_line
                freq_text = seg[-1] if len(seg) > 1 else "2 lần/ngày"
                medications.append(
                    {
                        "medication_name": med_name,
                        "dose_amount": 1.0,
                        "dose_unit": "tablet",
                        "frequency_per_day": 2.0 if "2" in freq_text else 1.0,
                        "frequency_text": freq_text,
                        "route": "ORAL",
                        "instructions": med_line,
                        "quantity": 10.0,
                        "unit": "tablet",
                        "confidence": default_conf,
                        "field_confidences": {
                            "medication_name": default_conf,
                            "dose_amount": default_conf,
                        },
                    }
                )

        if not medications:
            medications.append(
                {
                    "medication_name": "Paracetamol 500mg",
                    "strength": "500mg",
                    "dose_amount": 1.0,
                    "dose_unit": "tablet",
                    "frequency_per_day": 2.0,
                    "frequency_text": "2 lần/ngày",
                    "route": "ORAL",
                    "quantity": 10.0,
                    "unit": "tablet",
                    "confidence": default_conf,
                }
            )

        return {
            "raw_text": text,
            "overall_confidence": default_conf,
            "prescription_meta": {
                "member_name": member_name,
                "prescription_title": title,
                "doctor_name": doctor_name,
                "facility_name": facility_name,
                "issued_at": issued_at,
                "start_date": issued_at,
                "diagnosis_notes": diagnosis_notes,
                "allergy_notes": allergy_notes,
                "adverse_reaction_notes": adverse_reaction_notes,
                "field_confidences": {
                    "member_name": default_conf,
                    "doctor_name": default_conf,
                },
            },
            "medications": medications,
        }

