"""Local OCR engine for private prescription images and scanned PDFs."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from statistics import fmean
from typing import Any

from backend.app.core.config import settings
from backend.app.modules.imports.exceptions import ImportUnsupportedFileError


@dataclass(frozen=True)
class OCRDocumentResult:
    text: str
    confidence: float
    engine: str
    page_confidences: list[float]


class LocalTesseractOCREngine:
    """Extract searchable text locally without sending health data to a third party."""

    def extract(self, file_bytes: bytes, filename: str) -> OCRDocumentResult:
        if not settings.ocr_enabled:
            raise ImportUnsupportedFileError(
                "OCR ảnh/PDF đang bị tắt trên máy chủ. Vui lòng liên hệ quản trị viên."
            )
        if filename.casefold().endswith(".pdf") or file_bytes.startswith(b"%PDF"):
            return self._extract_pdf(file_bytes)
        return self._extract_image_document(file_bytes)

    def _extract_image_document(self, file_bytes: bytes) -> OCRDocumentResult:
        try:
            from PIL import Image, ImageSequence
        except ImportError as exc:
            raise self._dependency_error() from exc

        Image.MAX_IMAGE_PIXELS = settings.ocr_max_image_pixels
        try:
            source = Image.open(BytesIO(file_bytes))
            frames = []
            for index, frame in enumerate(ImageSequence.Iterator(source)):
                if index >= settings.ocr_pdf_max_pages:
                    raise ImportUnsupportedFileError(
                        f"Tệp ảnh có quá {settings.ocr_pdf_max_pages} trang/khung."
                    )
                frames.append(frame.copy())
        except ImportUnsupportedFileError:
            raise
        except Exception as exc:
            raise ImportUnsupportedFileError(
                "Không thể mở ảnh đơn thuốc. Hãy dùng PNG, JPEG, TIFF hoặc PDF hợp lệ."
            ) from exc

        if not frames:
            raise ImportUnsupportedFileError("Ảnh đơn thuốc không có nội dung.")
        return self._ocr_pages(frames, engine="tesseract-image")

    def _extract_pdf(self, file_bytes: bytes) -> OCRDocumentResult:
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise self._dependency_error() from exc

        try:
            reader = PdfReader(BytesIO(file_bytes), strict=False)
        except Exception as exc:
            raise ImportUnsupportedFileError("Tệp PDF không hợp lệ hoặc bị hỏng.") from exc

        page_count = len(reader.pages)
        if page_count == 0:
            raise ImportUnsupportedFileError("Tệp PDF không có trang nào.")
        if page_count > settings.ocr_pdf_max_pages:
            raise ImportUnsupportedFileError(
                f"PDF có {page_count} trang, vượt giới hạn {settings.ocr_pdf_max_pages} trang."
            )

        page_texts: list[str] = []
        page_confidences: list[float] = []
        used_tesseract = False
        for page_index, page in enumerate(reader.pages, start=1):
            try:
                embedded_text = (page.extract_text() or "").strip()
            except Exception:
                embedded_text = ""

            if self._has_meaningful_text(embedded_text):
                page_texts.append(embedded_text)
                page_confidences.append(0.99)
                continue

            rendered = self._render_pdf_page(file_bytes, page_index)
            page_result = self._ocr_pages(rendered, engine="tesseract-pdf")
            page_texts.append(page_result.text)
            page_confidences.append(page_result.confidence)
            used_tesseract = True

        combined = "\n\n".join(text for text in page_texts if text.strip()).strip()
        if not self._has_meaningful_text(combined):
            raise ImportUnsupportedFileError(
                "OCR không nhận được văn bản đủ rõ từ PDF. Hãy chụp lại tài liệu thẳng, đủ sáng và rõ nét."
            )
        return OCRDocumentResult(
            text=combined,
            confidence=round(fmean(page_confidences), 4),
            engine="pdf-text+tesseract" if used_tesseract else "pdf-text",
            page_confidences=page_confidences,
        )

    @staticmethod
    def _render_pdf_page(file_bytes: bytes, page_number: int) -> list[Any]:
        try:
            from pdf2image import convert_from_bytes
            from pdf2image.exceptions import (
                PDFInfoNotInstalledError,
                PDFPageCountError,
                PDFPopplerTimeoutError,
                PDFSyntaxError,
            )
        except ImportError as exc:
            raise LocalTesseractOCREngine._dependency_error() from exc

        try:
            return convert_from_bytes(
                file_bytes,
                dpi=settings.ocr_render_dpi,
                first_page=page_number,
                last_page=page_number,
                fmt="png",
                thread_count=1,
                timeout=settings.ocr_timeout_seconds,
                grayscale=True,
                poppler_path=settings.ocr_poppler_path,
            )
        except PDFInfoNotInstalledError as exc:
            raise ImportUnsupportedFileError(
                "Máy chủ thiếu Poppler để đọc PDF quét."
            ) from exc
        except PDFPopplerTimeoutError as exc:
            raise ImportUnsupportedFileError("Quá thời gian xử lý trang PDF.") from exc
        except (PDFPageCountError, PDFSyntaxError, ValueError) as exc:
            raise ImportUnsupportedFileError("Không thể kết xuất trang PDF để OCR.") from exc

    def _ocr_pages(self, images: list[Any], *, engine: str) -> OCRDocumentResult:
        texts: list[str] = []
        confidences: list[float] = []
        for image in images:
            text, confidence = self._ocr_image(image)
            if text.strip():
                texts.append(text.strip())
                confidences.append(confidence)

        combined = "\n\n".join(texts).strip()
        if not self._has_meaningful_text(combined):
            raise ImportUnsupportedFileError(
                "OCR không nhận được văn bản đủ rõ. Hãy chụp thẳng tài liệu, đủ sáng, không bị lóa và không bị cắt."
            )
        return OCRDocumentResult(
            text=combined,
            confidence=round(fmean(confidences), 4) if confidences else 0.0,
            engine=engine,
            page_confidences=confidences,
        )

    @staticmethod
    def _prepare_image(image: Any) -> Any:
        try:
            from PIL import Image, ImageOps
        except ImportError as exc:
            raise LocalTesseractOCREngine._dependency_error() from exc

        image = ImageOps.exif_transpose(image)
        if image.mode in {"RGBA", "LA"}:
            rgba = image.convert("RGBA")
            white = Image.new("RGBA", rgba.size, "white")
            image = Image.alpha_composite(white, rgba).convert("RGB")
        else:
            image = image.convert("RGB")

        width, height = image.size
        pixels = width * height
        if pixels > settings.ocr_max_image_pixels:
            scale = (settings.ocr_max_image_pixels / pixels) ** 0.5
            image = image.resize(
                (max(1, int(width * scale)), max(1, int(height * scale))),
                Image.Resampling.LANCZOS,
            )
        elif max(width, height) < 1800:
            scale = min(3.0, 1800 / max(width, height))
            image = image.resize(
                (max(1, int(width * scale)), max(1, int(height * scale))),
                Image.Resampling.LANCZOS,
            )

        gray = ImageOps.grayscale(image)
        gray = ImageOps.autocontrast(gray, cutoff=1)
        return ImageOps.expand(gray, border=20, fill="white")

    def _ocr_image(self, image: Any) -> tuple[str, float]:
        try:
            import pytesseract
            from pytesseract import Output
        except ImportError as exc:
            raise self._dependency_error() from exc

        if settings.ocr_tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = settings.ocr_tesseract_cmd

        prepared = self._prepare_image(image)
        try:
            requested_languages = settings.ocr_languages.split("+")
            if settings.ocr_tessdata_dir:
                tessdata_path = Path(settings.ocr_tessdata_dir).expanduser().resolve()
                if " " in str(tessdata_path):
                    raise ImportUnsupportedFileError(
                        "OCR_TESSDATA_DIR không được chứa khoảng trắng."
                    )
                tessdata_config = f"--tessdata-dir {tessdata_path.as_posix()}"
                missing = [
                    lang
                    for lang in requested_languages
                    if not (tessdata_path / f"{lang}.traineddata").is_file()
                ]
            else:
                tessdata_config = ""
                available_languages = set(pytesseract.get_languages(config=""))
                missing = [lang for lang in requested_languages if lang not in available_languages]
            if missing:
                raise ImportUnsupportedFileError(
                    "Máy chủ thiếu dữ liệu ngôn ngữ OCR: " + ", ".join(missing)
                )
            data = pytesseract.image_to_data(
                prepared,
                lang=settings.ocr_languages,
                config=f"--oem 1 --psm 6 -c preserve_interword_spaces=1 {tessdata_config}".strip(),
                output_type=Output.DICT,
                timeout=settings.ocr_timeout_seconds,
            )
        except ImportUnsupportedFileError:
            raise
        except pytesseract.TesseractNotFoundError as exc:
            raise ImportUnsupportedFileError(
                "Máy chủ chưa cài Tesseract OCR."
            ) from exc
        except pytesseract.TesseractError as exc:
            raise ImportUnsupportedFileError(f"Tesseract OCR thất bại: {exc}") from exc
        except RuntimeError as exc:
            raise ImportUnsupportedFileError("Quá thời gian xử lý OCR.") from exc

        lines: list[str] = []
        current_key: tuple[int, int, int, int] | None = None
        current_words: list[str] = []
        confidence_values: list[float] = []
        word_count = len(data.get("text", []))
        for index in range(word_count):
            word = str(data["text"][index] or "").strip()
            if not word:
                continue
            key = (
                int(data.get("page_num", [0] * word_count)[index]),
                int(data.get("block_num", [0] * word_count)[index]),
                int(data.get("par_num", [0] * word_count)[index]),
                int(data.get("line_num", [0] * word_count)[index]),
            )
            if current_key is not None and key != current_key:
                lines.append(" ".join(current_words))
                current_words = []
            current_key = key
            current_words.append(word)
            try:
                confidence = float(data.get("conf", [-1] * word_count)[index])
                if confidence >= 0:
                    confidence_values.append(confidence)
            except (TypeError, ValueError):
                pass
        if current_words:
            lines.append(" ".join(current_words))

        text = "\n".join(line for line in lines if line.strip())
        confidence = fmean(confidence_values) / 100 if confidence_values else 0.0
        return text, round(max(0.0, min(1.0, confidence)), 4)

    @staticmethod
    def _has_meaningful_text(text: str) -> bool:
        alphanumeric = sum(char.isalnum() for char in text)
        return alphanumeric >= 20 and len(text.split()) >= 4

    @staticmethod
    def _dependency_error() -> ImportUnsupportedFileError:
        return ImportUnsupportedFileError(
            "Máy chủ chưa cài đầy đủ thành phần OCR (Pillow, pytesseract, pypdf và pdf2image)."
        )
