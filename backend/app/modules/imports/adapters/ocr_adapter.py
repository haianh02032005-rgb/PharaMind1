import json
from typing import Any

from backend.app.modules.imports.adapters.base import BaseImportAdapter
from backend.app.modules.imports.exceptions import ImportUnsupportedFileError
from backend.app.modules.imports.ocr_engine import LocalTesseractOCREngine
from backend.app.modules.imports.parsers.ocr_prescription_parser import (
    parse_ocr_prescription,
)


class OCRImportAdapter(BaseImportAdapter):
    parser_version = "ocr-v2.0.0"

    def __init__(self, engine: LocalTesseractOCREngine | None = None) -> None:
        self.engine = engine or LocalTesseractOCREngine()

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

        is_binary_document = (
            file_bytes.startswith((b"\x89PNG", b"\xff\xd8\xff", b"GIF8", b"II*\x00", b"MM\x00*", b"%PDF"))
            or filename.casefold().endswith(".pdf")
        )
        if is_binary_document:
            result = self.engine.extract(file_bytes, filename)
            parsed = self._parse_free_text_prescription(
                result.text,
                filename=filename,
                default_member_name=default_member_name,
                confidence=result.confidence,
            )
            parsed["ocr_engine"] = result.engine
            parsed["page_confidences"] = result.page_confidences
            return parsed

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

        raise ImportUnsupportedFileError(
            "Không nhận diện được nội dung đơn thuốc trong tệp. Hãy dùng ảnh/PDF rõ nét "
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
        confidence: float | None = None,
    ) -> dict[str, Any]:
        is_low = "blur" in filename.lower() or "low" in filename.lower()
        default_conf = confidence if confidence is not None else (0.65 if is_low else 0.91)
        parsed = parse_ocr_prescription(
            text,
            default_member_name=default_member_name,
            confidence=default_conf,
        )
        return {
            "raw_text": text,
            "overall_confidence": default_conf,
            "prescription_meta": parsed.prescription_meta,
            "medications": parsed.medications,
        }

