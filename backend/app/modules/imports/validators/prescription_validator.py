from typing import Any

from backend.app.models.prescription import Prescription
from backend.app.modules.imports.enums import ImportMode, ValidationSeverity
from backend.app.modules.imports.normalizers.date_normalizer import parse_iso_date
from backend.app.modules.prescriptions.enums import PrescriptionStatus


def validate_prescription_header(
    *,
    member_resolution: dict[str, Any],
    prescription_draft: dict[str, Any],
    import_mode: str,
    target_prescription: Prescription | None,
    is_duplicate: bool,
    duplicate_of_import_id: int | None,
    duplicate_acknowledged: bool = False,
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []

    if not member_resolution.get("is_active", True):
        issues.append(
            {
                "severity": ValidationSeverity.BLOCKING.value,
                "code": "MEMBER_INACTIVE",
                "field_path": "member_id",
                "message": "Thành viên đang ở trạng thái INACTIVE, không thể nhập đơn thuốc mới.",
                "suggested_fix": "Kích hoạt lại hồ sơ thành viên hoặc chọn thành viên đang hoạt động.",
            }
        )

    if not member_resolution.get("is_resolved", True):
        ext_name = member_resolution.get("extracted_member_name") or "Không rõ"
        sel_name = member_resolution.get("selected_member_name") or ""
        issues.append(
            {
                "severity": ValidationSeverity.BLOCKING.value,
                "code": "MEMBER_MISMATCH",
                "field_path": "prescription.member_name",
                "message": (
                    f"Tên người bệnh trong tài liệu ('{ext_name}') không khớp với thành viên đang chọn ('{sel_name}'). "
                    "Vui lòng kiểm tra trước khi tiếp tục."
                ),
                "suggested_fix": "Xác nhận đúng thành viên nhận đơn thuốc hoặc quay lại Bước 1 để đổi thành viên.",
            }
        )

    if is_duplicate and not duplicate_acknowledged:
        issues.append(
            {
                "severity": ValidationSeverity.WARNING.value,
                "code": "DUPLICATE_FILE",
                "field_path": "source_file",
                "message": f"Tài liệu này đã được nhập trước đó (Phiên nhập #{duplicate_of_import_id}).",
                "suggested_fix": "Kiểm tra lại lịch sử nhập để tránh tạo trùng đơn thuốc.",
            }
        )

    start_dt = parse_iso_date(prescription_draft.get("start_date"))
    end_dt = parse_iso_date(prescription_draft.get("end_date"))
    if start_dt and end_dt and start_dt > end_dt:
        issues.append(
            {
                "severity": ValidationSeverity.ERROR.value,
                "code": "INVALID_DATE_RANGE",
                "field_path": "prescription.end_date",
                "message": "Ngày bắt đầu đơn thuốc không được lớn hơn ngày kết thúc.",
                "suggested_fix": "Chỉnh lại start_date <= end_date.",
            }
        )

    if import_mode == ImportMode.UPDATE_EXISTING_PRESCRIPTION.value:
        if target_prescription is None:
            issues.append(
                {
                    "severity": ValidationSeverity.BLOCKING.value,
                    "code": "TARGET_PRESCRIPTION_MISSING",
                    "field_path": "target_prescription_id",
                    "message": "Chưa chọn đơn thuốc hiện có để cập nhật.",
                    "suggested_fix": "Chọn một đơn thuốc đang ACTIVE của thành viên hoặc chuyển sang tạo đơn mới.",
                }
            )
        elif target_prescription.status in {
            PrescriptionStatus.ARCHIVED.value,
            PrescriptionStatus.COMPLETED.value,
        }:
            issues.append(
                {
                    "severity": ValidationSeverity.BLOCKING.value,
                    "code": "TARGET_PRESCRIPTION_NOT_EDITABLE",
                    "field_path": "target_prescription_id",
                    "message": f"Đơn thuốc đích #{target_prescription.id} đang ở trạng thái {target_prescription.status}, không thể cập nhật.",
                    "suggested_fix": "Chọn chế độ Tạo đơn thuốc mới (CREATE_NEW_PRESCRIPTION).",
                }
            )

    field_confs = prescription_draft.get("field_confidences") or {}
    for fname, conf in field_confs.items():
        try:
            c_val = float(conf)
        except (ValueError, TypeError):
            continue
        if c_val < 0.70 and not prescription_draft.get("user_edited"):
            issues.append(
                {
                    "severity": ValidationSeverity.WARNING.value,
                    "code": "LOW_OCR_CONFIDENCE_HEADER",
                    "field_path": f"prescription.{fname}",
                    "message": f"Độ tin cậy OCR thấp ({int(c_val * 100)}%) ở trường '{fname}'. Vui lòng kiểm tra lại.",
                    "suggested_fix": "Kiểm tra và chỉnh sửa trường thông tin trên giao diện rà soát.",
                }
            )

    return issues

