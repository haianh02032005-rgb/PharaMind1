"""Shared enums for PharmaMind AI.

Values are taken from docs/architecture/SYSTEM_FLOW.md and task specifications
so that every module (backend, hardware simulator, mobile, AI) uses the same
vocabulary.
"""

from enum import StrEnum


class FamilyRole(StrEnum):
    """Family workspace role (TASK 04 §7, §14)."""

    OWNER = "OWNER"
    ADMIN = "ADMIN"
    CAREGIVER = "CAREGIVER"
    VIEWER = "VIEWER"


class FamilyStatus(StrEnum):
    """Family workspace lifecycle status (TASK 04 §9, §14)."""

    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class MemberStatus(StrEnum):
    """Family member lifecycle status (TASK 05 §7)."""

    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class Gender(StrEnum):
    """Member biological/administrative gender (TASK 05 §10)."""

    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"
    UNSPECIFIED = "UNSPECIFIED"


class BloodType(StrEnum):
    """Member blood type (TASK 05 §12)."""

    A_POS = "A+"
    A_NEG = "A-"
    B_POS = "B+"
    B_NEG = "B-"
    AB_POS = "AB+"
    AB_NEG = "AB-"
    O_POS = "O+"
    O_NEG = "O-"
    UNKNOWN = "UNKNOWN"


class ConditionStatus(StrEnum):
    """Medical condition status (TASK 05 §17)."""

    ACTIVE = "ACTIVE"
    RESOLVED = "RESOLVED"
    UNKNOWN = "UNKNOWN"


class AllergyType(StrEnum):
    """Allergy category (TASK 05 §19)."""

    DRUG = "DRUG"
    FOOD = "FOOD"
    ENVIRONMENT = "ENVIRONMENT"
    OTHER = "OTHER"


class Severity(StrEnum):
    """Reported allergy or drug reaction severity (TASK 05 §20, §21)."""

    MILD = "MILD"
    MODERATE = "MODERATE"
    SEVERE = "SEVERE"
    UNKNOWN = "UNKNOWN"


class MedicationEventStatus(StrEnum):
    """Medication Event state machine (SYSTEM_FLOW §7, §16)."""

    SCHEDULED = "SCHEDULED"
    REMINDER_SENT = "REMINDER_SENT"
    CABINET_OPENED = "CABINET_OPENED"
    MEDICATION_RETRIEVED = "MEDICATION_RETRIEVED"
    USER_CONFIRMED = "USER_CONFIRMED"
    SNOOZED = "SNOOZED"
    SKIPPED = "SKIPPED"
    MISSED = "MISSED"


class CabinetEventType(StrEnum):
    """Events emitted by Hardware Simulator / ESP32 (SYSTEM_FLOW §13)."""

    CABINET_ONLINE = "CABINET_ONLINE"
    CABINET_OFFLINE = "CABINET_OFFLINE"
    COMPARTMENT_OPEN = "COMPARTMENT_OPEN"
    COMPARTMENT_CLOSE = "COMPARTMENT_CLOSE"
    LOW_STOCK = "LOW_STOCK"
    INVENTORY_UPDATED = "INVENTORY_UPDATED"


class InventoryStatus(StrEnum):
    """Compartment inventory level (SYSTEM_FLOW §10)."""

    NORMAL = "NORMAL"
    LOW_STOCK = "LOW_STOCK"
    CRITICAL = "CRITICAL"
    EMPTY = "EMPTY"


class ExpiryStatus(StrEnum):
    """Medication expiration status (SYSTEM_FLOW §11)."""

    NORMAL = "NORMAL"
    EXPIRING_SOON = "EXPIRING_SOON"
    EXPIRED = "EXPIRED"


class DosageForm(StrEnum):
    """Medication dosage form used to pick a 3D model (SYSTEM_FLOW §9)."""

    TABLET = "TABLET"
    OVAL_TABLET = "OVAL_TABLET"
    CAPSULE = "CAPSULE"
    SOFTGEL = "SOFTGEL"
    BOTTLE = "BOTTLE"
    BOX = "BOX"


# 3D model is for visualization only - never used to identify real medication.
DOSAGE_FORM_3D_MODEL: dict[DosageForm, str] = {
    DosageForm.TABLET: "tablet_round.glb",
    DosageForm.OVAL_TABLET: "tablet_oval.glb",
    DosageForm.CAPSULE: "capsule.glb",
    DosageForm.SOFTGEL: "softgel.glb",
    DosageForm.BOTTLE: "bottle.glb",
    DosageForm.BOX: "medicine_box.glb",
}
