from enum import StrEnum


class MedicationStatus(StrEnum):
    """Lifecycle and inventory status of a family medication (TASK 06 §14)."""

    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"
    DEPLETED = "DEPLETED"
    EXPIRED = "EXPIRED"


class MedicationUnit(StrEnum):
    """Inventory counting unit for a family medication (TASK 06 §15)."""

    TABLET = "TABLET"
    CAPSULE = "CAPSULE"
    ML = "ML"
    BOTTLE = "BOTTLE"
    BOX = "BOX"
    SACHET = "SACHET"
    VIAL = "VIAL"
    AMPULE = "AMPULE"
    PATCH = "PATCH"
    OTHER = "OTHER"


class DosageForm(StrEnum):
    """Pharmaceutical dosage form (TASK 06 §16)."""

    TABLET = "TABLET"
    OVAL_TABLET = "OVAL_TABLET"
    CAPSULE = "CAPSULE"
    SOFTGEL = "SOFTGEL"
    SYRUP = "SYRUP"
    SOLUTION = "SOLUTION"
    SUSPENSION = "SUSPENSION"
    CREAM = "CREAM"
    OINTMENT = "OINTMENT"
    GEL = "GEL"
    INJECTION = "INJECTION"
    DROPS = "DROPS"
    SPRAY = "SPRAY"
    PATCH = "PATCH"
    POWDER = "POWDER"
    SACHET = "SACHET"
    BOTTLE = "BOTTLE"
    BOX = "BOX"
    OTHER = "OTHER"


class MedicationSource(StrEnum):
    """Origin of a medication catalog entry (TASK 06 §11)."""

    USER_ENTERED = "USER_ENTERED"
    SEEDED = "SEEDED"
    IMPORTED = "IMPORTED"
    UNKNOWN = "UNKNOWN"

