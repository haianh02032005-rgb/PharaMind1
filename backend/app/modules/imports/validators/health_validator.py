from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.allergy_profile import AllergyProfile
from backend.app.modules.imports.enums import ValidationSeverity


def validate_health_candidates(
    db: Session,
    *,
    member_id: int,
    health_draft: dict[str, Any],
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []

    existing_allergies = list(
        db.scalars(select(AllergyProfile).where(AllergyProfile.member_id == member_id)).all()
    )

    # §19: If document says "No known allergy" while member already has recorded allergies -> emit HEALTH_CONFLICT warning
    if health_draft.get("has_no_known_allergy_note") and existing_allergies:
        allergen_names = ", ".join(a.allergen for a in existing_allergies)
        issues.append(
            {
                "severity": ValidationSeverity.WARNING.value,
                "code": "HEALTH_CONFLICT",
                "field_path": "health_updates.allergies",
                "message": (
                    f"Tài liệu ghi 'Không ghi nhận dị ứng' nhưng hồ sơ thành viên đang có dị ứng: {allergen_names}. "
                    "Hệ thống giữ nguyên dữ liệu dị ứng cũ để đảm bảo an toàn."
                ),
                "suggested_fix": "Không tự động xóa dị ứng đã lưu trong hồ sơ sức khỏe.",
            }
        )

    cond_count = len(health_draft.get("conditions") or [])
    allergy_count = len(health_draft.get("allergies") or [])
    rx_count = len(health_draft.get("drug_reactions") or [])

    if cond_count + allergy_count + rx_count > 0:
        issues.append(
            {
                "severity": ValidationSeverity.INFO.value,
                "code": "HEALTH_CANDIDATES_PENDING_REVIEW",
                "field_path": "health_updates",
                "message": (
                    f"Phát hiện {cond_count} chẩn đoán bệnh lý, {allergy_count} ghi chú dị ứng, "
                    f"và {rx_count} phản ứng thuốc từ đơn thuốc. Bạn có thể chọn xác nhận lưu vào Hồ sơ sức khỏe."
                ),
                "suggested_fix": "Xem và tích chọn tại Bước 4 (Cập nhật Hồ sơ sức khỏe).",
            }
        )

    return issues

