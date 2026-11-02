import re
from backend.app.modules.imports.normalizers.member_normalizer import strip_accents

STRENGTH_REGEX = re.compile(
    r"\b(\d+(?:[.,]\d+)?\s*(?:mg|mcg|g|ml|iu|%)(?:\s*/\s*\d+(?:[.,]\d+)?\s*(?:mg|mcg|g|ml|iu|%))?)\b",
    re.IGNORECASE,
)

KNOWN_INGREDIENTS: dict[str, str] = {
    "paracetamol": "Paracetamol",
    "panadol": "Paracetamol",
    "efferalgan": "Paracetamol",
    "hapacol": "Paracetamol",
    "tylenol": "Paracetamol",
    "amoxicillin": "Amoxicillin",
    "augmentin": "Amoxicillin + Clavulanic acid",
    "ibuprofen": "Ibuprofen",
    "omeprazole": "Omeprazole",
    "cetirizine": "Cetirizine",
    "loratadine": "Loratadine",
    "metformin": "Metformin",
    "amlodipine": "Amlodipine",
    "atorvastatin": "Atorvastatin",
    "vitamin c": "Ascorbic Acid",
}


def normalize_medication_key(name: str | None) -> str:
    if not name:
        return ""
    cleaned = strip_accents(str(name).strip().lower())
    cleaned = re.sub(r"[^a-z0-9]+", " ", cleaned).strip()
    return cleaned


def extract_strength_from_name(raw_name: str | None) -> tuple[str, str | None]:
    """Extract strength (e.g. 500mg) from a medication name string if embedded."""
    if not raw_name:
        return "", None
    text = str(raw_name).strip()
    match = STRENGTH_REGEX.search(text)
    if not match:
        return text, None
    strength = match.group(1).replace(" ", "")
    return text, strength


def infer_active_ingredient(
    medication_name: str | None,
    explicit_ingredient: str | None = None,
) -> str | None:
    if explicit_ingredient and str(explicit_ingredient).strip():
        return str(explicit_ingredient).strip()
    if not medication_name:
        return None
    norm = normalize_medication_key(medication_name)
    for keyword, ingredient in KNOWN_INGREDIENTS.items():
        if keyword in norm:
            return ingredient
    return None

