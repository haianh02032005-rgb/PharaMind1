from typing import Any

from backend.app.modules.imports.enums import ValidationSeverity
from backend.app.modules.imports.normalizers.date_normalizer import (
    normalize_time_string,
    parse_iso_date,
)


def validate_schedule_candidates(
    med_items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []

    for item in med_items:
        if item.get("action") == "SKIP":
            continue
        idx = item.get("row_index", 0)
        med_name = item.get("medication_name") or f"Thuốc #{idx + 1}"
        sched = item.get("schedule") or {}

        if not sched.get("create_schedule", False):
            continue

        raw_times = sched.get("schedule_times") or []
        if not raw_times:
            # Mandatory Rule §13.3: Do not guess schedule times — emit error requiring user input
            issues.append(
                {
                    "severity": ValidationSeverity.ERROR.value,
                    "code": "MISSING_SCHEDULE_TIMES",
                    "field_path": f"items[{idx}].schedule.schedule_times",
                    "message": f"Dòng thuốc #{idx + 1} ('{med_name}'): Chưa có khung giờ uống cụ thể. Vui lòng chọn giờ uống.",
                    "suggested_fix": "Chọn giờ uống cụ thể (ví dụ: 08:00, 20:00) tại Bước 3 (Lịch uống thuốc) hoặc tắt tạo lịch tự động cho thuốc này.",
                }
            )
        else:
            seen_times: set[str] = set()
            for t in raw_times:
                norm_t = normalize_time_string(str(t))
                if not norm_t:
                    issues.append(
                        {
                            "severity": ValidationSeverity.ERROR.value,
                            "code": "INVALID_SCHEDULE_TIME_FORMAT",
                            "field_path": f"items[{idx}].schedule.schedule_times",
                            "message": f"Dòng thuốc #{idx + 1} ('{med_name}'): Giờ uống '{t}' không đúng định dạng HH:MM (00:00 - 23:59).",
                            "suggested_fix": "Nhập giờ theo định dạng 24h HH:MM (ví dụ: 08:00).",
                        }
                    )
                elif norm_t in seen_times:
                    issues.append(
                        {
                            "severity": ValidationSeverity.ERROR.value,
                            "code": "DUPLICATE_SCHEDULE_TIME",
                            "field_path": f"items[{idx}].schedule.schedule_times",
                            "message": f"Dòng thuốc #{idx + 1} ('{med_name}'): Giờ uống '{norm_t}' bị lặp lại.",
                            "suggested_fix": "Xóa khung giờ bị trùng.",
                        }
                    )
                else:
                    seen_times.add(norm_t)

            freq_day = item.get("frequency_per_day")
            if freq_day is not None and seen_times:
                try:
                    expected_count = int(round(float(freq_day)))
                    if expected_count > 0 and len(seen_times) != expected_count:
                        issues.append(
                            {
                                "severity": ValidationSeverity.WARNING.value,
                                "code": "SCHEDULE_TIME_COUNT_MISMATCH",
                                "field_path": f"items[{idx}].schedule.schedule_times",
                                "message": (
                                    f"Dòng thuốc #{idx + 1} ('{med_name}'): Tần suất kê đơn là {expected_count} lần/ngày "
                                    f"nhưng đang chọn {len(seen_times)} khung giờ ({', '.join(sorted(seen_times))})."
                                ),
                                "suggested_fix": f"Điều chỉnh đủ {expected_count} khung giờ uống mỗi ngày.",
                            }
                        )
                except (ValueError, TypeError):
                    pass

        start_dt = parse_iso_date(sched.get("start_date"))
        end_dt = parse_iso_date(sched.get("end_date"))
        if not start_dt:
            issues.append(
                {
                    "severity": ValidationSeverity.ERROR.value,
                    "code": "MISSING_SCHEDULE_START_DATE",
                    "field_path": f"items[{idx}].schedule.start_date",
                    "message": f"Dòng thuốc #{idx + 1} ('{med_name}'): Lịch nhắc uống thuốc cần có ngày bắt đầu (start_date).",
                    "suggested_fix": "Chọn ngày bắt đầu lịch uống thuốc.",
                }
            )
        elif end_dt and start_dt > end_dt:
            issues.append(
                {
                    "severity": ValidationSeverity.ERROR.value,
                    "code": "INVALID_SCHEDULE_DATE_RANGE",
                    "field_path": f"items[{idx}].schedule.end_date",
                    "message": f"Dòng thuốc #{idx + 1} ('{med_name}'): Ngày kết thúc lịch uống không được nhỏ hơn ngày bắt đầu.",
                    "suggested_fix": "Chỉnh lại ngày kết thúc >= ngày bắt đầu.",
                }
            )

    return issues

