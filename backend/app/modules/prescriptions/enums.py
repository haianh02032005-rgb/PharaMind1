from enum import StrEnum


class PrescriptionStatus(StrEnum):
    """Lifecycle status of a prescription (TASK 07 §7)."""

    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"


class MedicationRoute(StrEnum):
    """Administration route of a prescribed medication (TASK 07 §13)."""

    ORAL = "ORAL"
    TOPICAL = "TOPICAL"
    INHALATION = "INHALATION"
    INJECTION = "INJECTION"
    EYE = "EYE"
    EAR = "EAR"
    NASAL = "NASAL"
    RECTAL = "RECTAL"
    SUBLINGUAL = "SUBLINGUAL"
    TRANSDERMAL = "TRANSDERMAL"
    OTHER = "OTHER"


class DoseUnit(StrEnum):
    """Dosage unit for a prescription item (TASK 07 §10)."""

    TABLET = "TABLET"
    CAPSULE = "CAPSULE"
    ML = "ML"
    BOTTLE = "BOTTLE"
    BOX = "BOX"
    SACHET = "SACHET"
    VIAL = "VIAL"
    AMPULE = "AMPULE"
    DROP = "DROP"
    PUFF = "PUFF"
    PATCH = "PATCH"
    OTHER = "OTHER"

