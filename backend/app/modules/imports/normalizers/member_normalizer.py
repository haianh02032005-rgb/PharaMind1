import re
import unicodedata


def strip_accents(value: str) -> str:
    if not value:
        return ""
    text = value.replace("đ", "d").replace("Đ", "D")
    normalized = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


def normalize_member_name(value: str | None) -> str:
    if not value:
        return ""
    cleaned = re.sub(r"\s+", " ", str(value).strip())
    return strip_accents(cleaned).lower()


def names_match(extracted_name: str | None, member_full_name: str | None) -> tuple[bool, float]:
    """Compare extracted patient name against selected FamilyMember full_name."""
    if not extracted_name or not str(extracted_name).strip():
        # No name extracted in document -> neutral
        return True, 1.0

    norm_ext = normalize_member_name(extracted_name)
    norm_mem = normalize_member_name(member_full_name)

    if not norm_mem:
        return False, 0.0

    if norm_ext == norm_mem:
        return True, 1.0

    # Token overlap check for partial match (e.g. "Minh An" vs "Nguyen Minh An")
    ext_tokens = set(norm_ext.split())
    mem_tokens = set(norm_mem.split())
    if ext_tokens and mem_tokens:
        overlap = len(ext_tokens & mem_tokens) / max(len(ext_tokens), len(mem_tokens))
        if overlap >= 0.75:
            return True, round(overlap, 2)
        return False, round(overlap, 2)

    return False, 0.0

