from typing import Any

from backend.app.models.family_member import FamilyMember
from backend.app.modules.imports.normalizers.member_normalizer import names_match
from backend.app.shared.enums import MemberStatus


def resolve_member_identity(
    member: FamilyMember,
    prescription_meta: dict[str, Any],
    *,
    user_confirmed_override: bool = False,
) -> dict[str, Any]:
    """Compare extracted member name/identifier against the selected FamilyMember (§8)."""
    extracted_name = prescription_meta.get("member_name")
    extracted_identifier = prescription_meta.get("member_identifier")

    is_active = member.status == MemberStatus.ACTIVE.value
    matched, score = names_match(extracted_name, member.full_name)

    id_mismatch = False
    if extracted_identifier and str(extracted_identifier).strip():
        raw_id = str(extracted_identifier).strip().upper()
        # Accept MEM-<id> or exact numeric id or match if not conflicting with another explicit ID
        expected_tokens = {str(member.id), f"MEM-{member.id}", f"MEM-{member.id:03d}"}
        if raw_id.isdigit() and int(raw_id) != member.id:
            id_mismatch = True

    is_match = (matched and not id_mismatch) or user_confirmed_override

    return {
        "selected_member_id": member.id,
        "selected_member_name": member.full_name,
        "selected_member_status": member.status,
        "extracted_member_name": extracted_name,
        "extracted_member_identifier": extracted_identifier,
        "is_active": is_active,
        "name_matched": matched,
        "match_score": score,
        "id_mismatch": id_mismatch,
        "is_resolved": is_match and is_active,
        "user_confirmed_override": user_confirmed_override,
    }

