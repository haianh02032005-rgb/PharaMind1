import re
from typing import Any


NO_ALLERGY_PATTERNS = (
    "no known allergy",
    "nkda",
    "không dị ứng",
    "khong di ung",
    "chưa ghi nhận dị ứng",
    "chua ghi nhan di ung",
    "none",
)


def parse_health_candidates(
    raw_meta: dict[str, Any],
    raw_items: list[dict[str, Any]],
) -> dict[str, Any]:
    """Extract optional MedicalCondition, AllergyProfile, and DrugReactionHistory candidates (§14)."""
    diagnosis_texts: list[str] = []
    allergy_texts: list[str] = []
    reaction_texts: list[str] = []

    if raw_meta.get("diagnosis_notes"):
        diagnosis_texts.append(str(raw_meta["diagnosis_notes"]).strip())
    if raw_meta.get("allergy_notes"):
        allergy_texts.append(str(raw_meta["allergy_notes"]).strip())
    if raw_meta.get("adverse_reaction_notes"):
        reaction_texts.append(str(raw_meta["adverse_reaction_notes"]).strip())

    for item in raw_items:
        d = (item.get("diagnosis_notes") or "").strip()
        if d and d not in diagnosis_texts:
            diagnosis_texts.append(d)
        a = (item.get("allergy_notes") or "").strip()
        if a and a not in allergy_texts:
            allergy_texts.append(a)
        r = (item.get("adverse_reaction_notes") or "").strip()
        if r and r not in reaction_texts:
            reaction_texts.append(r)

    conditions: list[dict[str, Any]] = []
    for text in diagnosis_texts:
        for part in re.split(r"[;\n,]+", text):
            name = part.strip()
            if name and len(name) >= 2:
                conditions.append(
                    {
                        "name": name,
                        "diagnosed_at": raw_meta.get("issued_at"),
                        "status": "ACTIVE",
                        "notes": "Trích xuất từ đơn thuốc nhập",
                        "confirmed": False,
                    }
                )

    allergies: list[dict[str, Any]] = []
    has_no_known_allergy_note = False
    for text in allergy_texts:
        lower_txt = text.lower().strip()
        if any(pat in lower_txt for pat in NO_ALLERGY_PATTERNS):
            has_no_known_allergy_note = True
            continue
        for part in re.split(r"[;\n,]+", text):
            cleaned = re.sub(
                r"^(?:dị ứng|di ung|allergy|allergies)\s*[:\-]?\s*",
                "",
                part.strip(),
                flags=re.IGNORECASE,
            ).strip()
            if cleaned and len(cleaned) >= 2:
                allergies.append(
                    {
                        "allergen": cleaned,
                        "allergy_type": "DRUG",
                        "severity": "MODERATE",
                        "reaction_description": f"Ghi chú đơn thuốc: {part.strip()}",
                        "notes": "Trích xuất từ đơn thuốc nhập",
                        "confirmed": False,
                    }
                )

    drug_reactions: list[dict[str, Any]] = []
    for text in reaction_texts:
        for part in re.split(r"[;\n]+", text):
            cleaned = part.strip()
            if not cleaned:
                continue
            # Try splitting "Drug: Reaction" or "Drug - Reaction"
            if ":" in cleaned:
                drug_part, react_part = cleaned.split(":", 1)
            elif "-" in cleaned:
                drug_part, react_part = cleaned.split("-", 1)
            else:
                drug_part, react_part = cleaned, cleaned
            drug_reactions.append(
                {
                    "drug_name": drug_part.strip() or "Thuốc ghi trong đơn",
                    "active_ingredient": None,
                    "reaction": react_part.strip() or cleaned,
                    "severity": "MODERATE",
                    "occurred_at": raw_meta.get("issued_at"),
                    "notes": "Trích xuất từ đơn thuốc nhập",
                    "confirmed": False,
                }
            )

    return {
        "confirm_conditions": False,
        "conditions": conditions,
        "confirm_allergies": False,
        "allergies": allergies,
        "confirm_drug_reactions": False,
        "drug_reactions": drug_reactions,
        "has_no_known_allergy_note": has_no_known_allergy_note,
        "general_notes_append": None,
    }

