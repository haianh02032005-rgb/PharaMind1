import re

UNIT_SYNONYMS: dict[str, str] = {
    "vien": "tablet",
    "viên": "tablet",
    "vien nen": "tablet",
    "viên nén": "tablet",
    "tablet": "tablet",
    "tablets": "tablet",
    "tab": "tablet",
    "vien nang": "capsule",
    "viên nang": "capsule",
    "capsule": "capsule",
    "capsules": "capsule",
    "cap": "capsule",
    "ml": "ml",
    "mg": "mg",
    "g": "g",
    "mcg": "mcg",
    "giot": "drop",
    "giọt": "drop",
    "drop": "drop",
    "drops": "drop",
    "nhát xịt": "puff",
    "nhat xit": "puff",
    "puff": "puff",
    "goi": "unit",
    "gói": "unit",
    "ong": "unit",
    "ống": "unit",
    "unit": "unit",
}

DOSAGE_FORM_SYNONYMS: dict[str, str] = {
    "tablet": "TABLET",
    "vien nen": "TABLET",
    "viên nén": "TABLET",
    "viên": "TABLET",
    "capsule": "CAPSULE",
    "vien nang": "CAPSULE",
    "viên nang": "CAPSULE",
    "syrup": "SYRUP",
    "siro": "SYRUP",
    "drops": "DROPS",
    "drop": "DROPS",
    "nhỏ giọt": "DROPS",
    "ointment": "OINTMENT",
    "kem bôi": "OINTMENT",
    "inhaler": "INHALER",
    "xịt": "INHALER",
    "injection": "INJECTION",
    "tiêm": "INJECTION",
    "powder": "POWDER",
    "bột": "POWDER",
    "gói bột": "POWDER",
    "other": "OTHER",
}

ROUTE_SYNONYMS: dict[str, str] = {
    "oral": "ORAL",
    "uong": "ORAL",
    "uống": "ORAL",
    "duong uong": "ORAL",
    "đường uống": "ORAL",
    "topical": "TOPICAL",
    "boi": "TOPICAL",
    "bôi": "TOPICAL",
    "ngoai da": "TOPICAL",
    "inhalation": "INHALATION",
    "hit": "INHALATION",
    "hít": "INHALATION",
    "xit": "INHALATION",
    "xịt": "INHALATION",
    "injection": "INJECTION",
    "tiem": "INJECTION",
    "tiêm": "INJECTION",
    "eye": "EYE",
    "nho mat": "EYE",
    "nhỏ mắt": "EYE",
    "ear": "EAR",
    "nho tai": "EAR",
    "nhỏ tai": "EAR",
    "nasal": "NASAL",
    "nho mui": "NASAL",
    "nhỏ mũi": "NASAL",
    "xit mui": "NASAL",
    "xịt mũi": "NASAL",
    "other": "OTHER",
}


def normalize_unit(raw_unit: str | None) -> str:
    if not raw_unit:
        return "tablet"
    cleaned = str(raw_unit).strip().lower()
    return UNIT_SYNONYMS.get(cleaned, cleaned if cleaned in {"tablet", "capsule", "ml", "mg", "drop", "puff", "unit"} else "tablet")


def normalize_dosage_form(raw_form: str | None, fallback_unit: str | None = None) -> str:
    if raw_form:
        cleaned = str(raw_form).strip().lower()
        if cleaned.upper() in {
            "TABLET",
            "CAPSULE",
            "SYRUP",
            "DROPS",
            "OINTMENT",
            "INHALER",
            "INJECTION",
            "POWDER",
            "OTHER",
        }:
            return cleaned.upper()
        if cleaned in DOSAGE_FORM_SYNONYMS:
            return DOSAGE_FORM_SYNONYMS[cleaned]

    if fallback_unit:
        unit_norm = normalize_unit(fallback_unit)
        if unit_norm == "capsule":
            return "CAPSULE"
        if unit_norm == "ml":
            return "SYRUP"
        if unit_norm == "drop":
            return "DROPS"
        if unit_norm == "puff":
            return "INHALER"
    return "TABLET"


def normalize_route(raw_route: str | None) -> str:
    if not raw_route:
        return "ORAL"
    cleaned = str(raw_route).strip().lower()
    if cleaned.upper() in {
        "ORAL",
        "TOPICAL",
        "INHALATION",
        "INJECTION",
        "EYE",
        "EAR",
        "NASAL",
        "OTHER",
    }:
        return cleaned.upper()
    return ROUTE_SYNONYMS.get(cleaned, "ORAL")


def parse_frequency_per_day(
    freq_value: float | int | str | None,
    frequency_text: str | None = None,
) -> float | None:
    if freq_value is not None and str(freq_value).strip() != "":
        try:
            val = float(freq_value)
            if val > 0:
                return val
        except (ValueError, TypeError):
            pass

    if frequency_text:
        txt = str(frequency_text).lower()
        m = re.search(r"(\d+(?:\.\d+)?)\s*(?:lần|lan|times?)\s*/?\s*(?:ngày|ngay|day)", txt)
        if m:
            return float(m.group(1))
        # Count period keywords like sáng, trưa, chiều, tối
        periods = [p for p in ("sáng", "sang", "trưa", "trua", "chiều", "chieu", "tối", "toi") if p in txt]
        if periods:
            # Deduplicate accented/unaccented pairs
            unique_periods = set()
            if "sáng" in txt or "sang" in txt:
                unique_periods.add("morning")
            if "trưa" in txt or "trua" in txt:
                unique_periods.add("noon")
            if "chiều" in txt or "chieu" in txt:
                unique_periods.add("afternoon")
            if "tối" in txt or "toi" in txt:
                unique_periods.add("evening")
            if unique_periods:
                return float(len(unique_periods))
    return None

