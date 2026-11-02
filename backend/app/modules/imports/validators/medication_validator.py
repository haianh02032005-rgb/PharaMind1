from typing import Any

from backend.app.modules.imports.enums import ValidationSeverity
from backend.app.modules.imports.normalizers.medication_normalizer import (
    normalize_medication_key,
)


def validate_medication_items(
    med_items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []

    active_items = [it for it in med_items if it.get("action") != "SKIP"]
    if not active_items:
        issues.append(
            {
                "severity": ValidationSeverity.BLOCKING.value,
                "code": "EMPTY_MEDICATION_LIST",
                "field_path": "items",
                "message": "Đơn thuốc phải có ít nhất 1 thuốc được chọn để lưu.",
                "suggested_fix": "Thêm hoặc bỏ trạng thái bỏ qua (SKIP) ít nhất 1 dòng thuốc.",
            }
        )
        return issues

    seen_med_keys: dict[str, int] = {}

    for item in active_items:
        idx = item.get("row_index", 0)
        med_name = (item.get("medication_name") or "").strip()
        if not med_name:
            issues.append(
                {
                    "severity": ValidationSeverity.ERROR.value,
                    "code": "MISSING_MEDICATION_NAME",
                    "field_path": f"items[{idx}].medication_name",
                    "message": f"Dòng thuốc #{idx + 1}: Thiếu tên thuốc.",
                    "suggested_fix": "Nhập tên thuốc rõ ràng.",
                }
            )
        else:
            key = (
                f"id:{item['family_medication_id']}"
                if item.get("family_medication_id")
                else f"name:{normalize_medication_key(med_name)}:{(item.get('strength') or '').strip().lower()}"
            )
            if key in seen_med_keys:
                prev_idx = seen_med_keys[key]
                issues.append(
                    {
                        "severity": ValidationSeverity.ERROR.value,
                        "code": "DUPLICATE_MEDICATION_IN_PRESCRIPTION",
                        "field_path": f"items[{idx}].medication_name",
                        "message": f"Dòng thuốc #{idx + 1} ('{med_name}') bị trùng với dòng #{prev_idx + 1} trong cùng đơn thuốc.",
                        "suggested_fix": "Gộp liều dùng hoặc đặt trạng thái Bỏ qua (SKIP) cho dòng thuốc trùng.",
                    }
                )
            else:
                seen_med_keys[key] = idx

        dose_amount = item.get("dose_amount")
        try:
            dose_val = float(dose_amount) if dose_amount is not None else 0.0
        except (ValueError, TypeError):
            dose_val = 0.0

        if dose_val <= 0:
            issues.append(
                {
                    "severity": ValidationSeverity.ERROR.value,
                    "code": "INVALID_DOSE_AMOUNT",
                    "field_path": f"items[{idx}].dose_amount",
                    "message": f"Dòng thuốc #{idx + 1} ('{med_name or 'Chưa rõ'}'): Liều dùng mỗi lần (dose_amount) phải lớn hơn 0.",
                    "suggested_fix": "Nhập số lượng liều dùng hợp lệ (ví dụ: 1 viên, 5 ml).",
                }
            )

        if not (item.get("dose_unit") or "").strip():
            issues.append(
                {
                    "severity": ValidationSeverity.ERROR.value,
                    "code": "MISSING_DOSE_UNIT",
                    "field_path": f"items[{idx}].dose_unit",
                    "message": f"Dòng thuốc #{idx + 1}: Thiếu đơn vị liều dùng (dose_unit).",
                    "suggested_fix": "Chọn đơn vị liều dùng (tablet, capsule, ml...).",
                }
            )

        freq_day = item.get("frequency_per_day")
        freq_txt = (item.get("frequency_text") or "").strip()
        has_valid_freq = False
        if freq_day is not None:
            try:
                if float(freq_day) > 0:
                    has_valid_freq = True
            except (ValueError, TypeError):
                pass
        if not has_valid_freq and not freq_txt:
            issues.append(
                {
                    "severity": ValidationSeverity.ERROR.value,
                    "code": "MISSING_FREQUENCY",
                    "field_path": f"items[{idx}].frequency_per_day",
                    "message": f"Dòng thuốc #{idx + 1}: Thiếu số lần uống mỗi ngày hoặc mô tả tần suất.",
                    "suggested_fix": "Nhập số lần/ngày (ví dụ: 2) hoặc hướng dẫn tần suất.",
                }
            )

        qty = item.get("quantity")
        if qty is not None:
            try:
                if float(qty) < 0:
                    issues.append(
                        {
                            "severity": ValidationSeverity.ERROR.value,
                            "code": "INVALID_QUANTITY",
                            "field_path": f"items[{idx}].quantity",
                            "message": f"Dòng thuốc #{idx + 1}: Số lượng thuốc trong tủ không được âm.",
                            "suggested_fix": "Nhập số lượng >= 0.",
                        }
                    )
            except (ValueError, TypeError):
                pass

        # OCR Confidence checks (§10.2)
        conf = float(item.get("confidence", 1.0))
        if conf < 0.70 and not item.get("user_edited"):
            issues.append(
                {
                    "severity": ValidationSeverity.WARNING.value,
                    "code": "LOW_OCR_CONFIDENCE_MEDICATION",
                    "field_path": f"items[{idx}].medication_name",
                    "message": f"Dòng thuốc #{idx + 1} ('{med_name}'): Độ tin cậy OCR thấp ({int(conf * 100)}%). Cần kiểm tra kỹ tên thuốc, hàm lượng và liều dùng.",
                    "suggested_fix": "Chỉnh sửa hoặc xác nhận thông tin dòng thuốc này.",
                }
            )
        elif conf < 0.85 and not item.get("user_edited"):
            issues.append(
                {
                    "severity": ValidationSeverity.INFO.value,
                    "code": "MEDIUM_OCR_CONFIDENCE_MEDICATION",
                    "field_path": f"items[{idx}].medication_name",
                    "message": f"Dòng thuốc #{idx + 1} ('{med_name}'): Độ tin cậy OCR trung bình ({int(conf * 100)}%).",
                    "suggested_fix": "Rà soát nhanh thông tin liều dùng.",
                }
            )

        # Allergy & Drug reaction warnings (§16)
        for warning_msg in item.get("allergy_warnings") or []:
            issues.append(
                {
                    "severity": ValidationSeverity.WARNING.value,
                    "code": "ALLERGY_MEDICATION_CONFLICT",
                    "field_path": f"items[{idx}].medication_name",
                    "message": f"Cảnh báo dị ứng ở dòng thuốc #{idx + 1} ('{med_name}'): {warning_msg}",
                    "suggested_fix": "Tham khảo ý kiến bác sĩ hoặc chọn Bỏ qua (SKIP) nếu thuốc chống chỉ định.",
                }
            )
        for rx_msg in item.get("reaction_warnings") or []:
            issues.append(
                {
                    "severity": ValidationSeverity.WARNING.value,
                    "code": "DRUG_REACTION_CONFLICT",
                    "field_path": f"items[{idx}].medication_name",
                    "message": f"Cảnh báo phản ứng thuốc ở dòng #{idx + 1} ('{med_name}'): {rx_msg}",
                    "suggested_fix": "Kiểm tra lại tiền sử phản ứng thuốc của thành viên.",
                }
            )

    return issues

