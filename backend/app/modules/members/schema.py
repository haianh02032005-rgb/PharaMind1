from datetime import date, datetime
import re

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

from backend.app.shared.enums import (
    AllergyType,
    BloodType,
    ConditionStatus,
    Gender,
    Severity,
)


PHONE_REGEX = re.compile(r"^\+?[0-9][0-9\s\-]{2,29}$")


def _strip_non_empty(value: str, field_name: str = "Field") -> str:
    stripped = value.strip()
    if not stripped:
        raise ValueError(f"{field_name} must not be empty")
    return stripped


def _validate_not_future_date(value: date | None) -> date | None:
    if value is not None and value > date.today():
        raise ValueError("Date cannot be in the future")
    return value


def _validate_phone(value: str) -> str:
    stripped = value.strip()
    if not stripped or len(stripped) > 30 or not PHONE_REGEX.match(stripped):
        raise ValueError("Invalid phone number")
    digits = [ch for ch in stripped if ch.isdigit()]
    if len(digits) < 3:
        raise ValueError("Invalid phone number")
    return stripped


# ---------------------------------------------------------------------------
# Health Profile Schemas
# ---------------------------------------------------------------------------


class HealthProfileUpdateRequest(BaseModel):
    blood_type: BloodType | None = None
    height_cm: float | None = Field(default=None, gt=0, le=300)
    weight_kg: float | None = Field(default=None, gt=0, le=500)
    general_notes: str | None = None

    model_config = ConfigDict(extra="forbid")


class HealthProfileResponse(BaseModel):
    id: int
    member_id: int
    blood_type: str | None = None
    height_cm: float | None = None
    weight_kg: float | None = None
    general_notes: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def bmi(self) -> float | None:
        if (
            self.height_cm is not None
            and self.height_cm > 0
            and self.weight_kg is not None
            and self.weight_kg > 0
        ):
            height_m = self.height_cm / 100.0
            return round(self.weight_kg / (height_m * height_m), 2)
        return None


# ---------------------------------------------------------------------------
# FamilyMember Schemas
# ---------------------------------------------------------------------------


class MemberCreateRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=150)
    date_of_birth: date | None = None
    gender: Gender | None = None
    relationship_label: str | None = Field(default=None, max_length=50)
    avatar_url: str | None = Field(default=None, max_length=500)

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, value: str) -> str:
        return _strip_non_empty(value, "full_name")

    @field_validator("date_of_birth")
    @classmethod
    def validate_dob(cls, value: date | None) -> date | None:
        return _validate_not_future_date(value)

    @field_validator("relationship_label")
    @classmethod
    def validate_relationship_label(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None


class MemberUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=150)
    date_of_birth: date | None = None
    gender: Gender | None = None
    relationship_label: str | None = Field(default=None, max_length=50)
    avatar_url: str | None = Field(default=None, max_length=500)

    model_config = ConfigDict(extra="forbid")

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _strip_non_empty(value, "full_name")

    @field_validator("date_of_birth")
    @classmethod
    def validate_dob(cls, value: date | None) -> date | None:
        return _validate_not_future_date(value)

    @field_validator("relationship_label")
    @classmethod
    def validate_relationship_label(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None


class MemberResponse(BaseModel):
    id: int
    family_id: int
    full_name: str
    date_of_birth: date | None = None
    gender: str | None = None
    relationship_label: str | None = None
    avatar_url: str | None = None
    status: str
    health_profile: HealthProfileResponse | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MemberListItem(BaseModel):
    id: int
    family_id: int
    full_name: str
    date_of_birth: date | None = None
    gender: str | None = None
    relationship_label: str | None = None
    avatar_url: str | None = None
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MemberListResponse(BaseModel):
    items: list[MemberListItem]


# ---------------------------------------------------------------------------
# MedicalCondition Schemas
# ---------------------------------------------------------------------------


class MedicalConditionCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    diagnosed_at: date | None = None
    status: ConditionStatus = ConditionStatus.ACTIVE
    notes: str | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return _strip_non_empty(value, "name")

    @field_validator("diagnosed_at")
    @classmethod
    def validate_diagnosed_at(cls, value: date | None) -> date | None:
        return _validate_not_future_date(value)


class MedicalConditionUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    diagnosed_at: date | None = None
    status: ConditionStatus | None = None
    notes: str | None = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _strip_non_empty(value, "name")

    @field_validator("diagnosed_at")
    @classmethod
    def validate_diagnosed_at(cls, value: date | None) -> date | None:
        return _validate_not_future_date(value)


class MedicalConditionResponse(BaseModel):
    id: int
    member_id: int
    name: str
    diagnosed_at: date | None = None
    status: str
    notes: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MedicalConditionListResponse(BaseModel):
    items: list[MedicalConditionResponse]


# ---------------------------------------------------------------------------
# AllergyProfile Schemas
# ---------------------------------------------------------------------------


class AllergyCreateRequest(BaseModel):
    allergen: str = Field(min_length=1, max_length=200)
    allergy_type: AllergyType = AllergyType.OTHER
    severity: Severity = Severity.UNKNOWN
    reaction_description: str | None = None
    recorded_at: date | None = None
    source: str | None = Field(default=None, max_length=100)
    notes: str | None = None

    @field_validator("allergen")
    @classmethod
    def validate_allergen(cls, value: str) -> str:
        return _strip_non_empty(value, "allergen")

    @field_validator("recorded_at")
    @classmethod
    def validate_recorded_at(cls, value: date | None) -> date | None:
        return _validate_not_future_date(value)


class AllergyUpdateRequest(BaseModel):
    allergen: str | None = Field(default=None, min_length=1, max_length=200)
    allergy_type: AllergyType | None = None
    severity: Severity | None = None
    reaction_description: str | None = None
    recorded_at: date | None = None
    source: str | None = Field(default=None, max_length=100)
    notes: str | None = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("allergen")
    @classmethod
    def validate_allergen(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _strip_non_empty(value, "allergen")

    @field_validator("recorded_at")
    @classmethod
    def validate_recorded_at(cls, value: date | None) -> date | None:
        return _validate_not_future_date(value)


class AllergyResponse(BaseModel):
    id: int
    member_id: int
    allergen: str
    allergy_type: str
    severity: str
    reaction_description: str | None = None
    recorded_at: date | None = None
    source: str | None = None
    notes: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AllergyListResponse(BaseModel):
    items: list[AllergyResponse]


# ---------------------------------------------------------------------------
# DrugReactionHistory Schemas
# ---------------------------------------------------------------------------


class DrugReactionCreateRequest(BaseModel):
    drug_name: str = Field(min_length=1, max_length=200)
    active_ingredient: str | None = Field(default=None, max_length=200)
    reaction: str = Field(min_length=1)
    severity: Severity = Severity.UNKNOWN
    occurred_at: date | None = None
    confirmed_by_professional: bool = False
    notes: str | None = None

    @field_validator("drug_name")
    @classmethod
    def validate_drug_name(cls, value: str) -> str:
        return _strip_non_empty(value, "drug_name")

    @field_validator("reaction")
    @classmethod
    def validate_reaction(cls, value: str) -> str:
        return _strip_non_empty(value, "reaction")

    @field_validator("occurred_at")
    @classmethod
    def validate_occurred_at(cls, value: date | None) -> date | None:
        return _validate_not_future_date(value)


class DrugReactionUpdateRequest(BaseModel):
    drug_name: str | None = Field(default=None, min_length=1, max_length=200)
    active_ingredient: str | None = Field(default=None, max_length=200)
    reaction: str | None = Field(default=None, min_length=1)
    severity: Severity | None = None
    occurred_at: date | None = None
    confirmed_by_professional: bool | None = None
    notes: str | None = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("drug_name")
    @classmethod
    def validate_drug_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _strip_non_empty(value, "drug_name")

    @field_validator("reaction")
    @classmethod
    def validate_reaction(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _strip_non_empty(value, "reaction")

    @field_validator("occurred_at")
    @classmethod
    def validate_occurred_at(cls, value: date | None) -> date | None:
        return _validate_not_future_date(value)


class DrugReactionResponse(BaseModel):
    id: int
    member_id: int
    drug_name: str
    active_ingredient: str | None = None
    reaction: str
    severity: str
    occurred_at: date | None = None
    confirmed_by_professional: bool
    notes: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DrugReactionListResponse(BaseModel):
    items: list[DrugReactionResponse]


# ---------------------------------------------------------------------------
# EmergencyContact Schemas
# ---------------------------------------------------------------------------


class EmergencyContactCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    relationship: str | None = Field(default=None, max_length=50)
    phone: str = Field(min_length=3, max_length=30)
    is_primary: bool = False

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return _strip_non_empty(value, "name")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        return _validate_phone(value)


class EmergencyContactUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    relationship: str | None = Field(default=None, max_length=50)
    phone: str | None = Field(default=None, min_length=3, max_length=30)
    is_primary: bool | None = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _strip_non_empty(value, "name")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _validate_phone(value)


class EmergencyContactResponse(BaseModel):
    id: int
    member_id: int
    name: str
    relationship: str | None = None
    phone: str
    is_primary: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EmergencyContactListResponse(BaseModel):
    items: list[EmergencyContactResponse]
