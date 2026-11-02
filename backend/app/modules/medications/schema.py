from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

from backend.app.modules.medications.enums import (
    DosageForm,
    MedicationStatus,
    MedicationUnit,
)


def _strip_non_empty(value: str, field_name: str = "Field") -> str:
    stripped = value.strip()
    if not stripped:
        raise ValueError(f"{field_name} must not be empty")
    return stripped


def _strip_optional(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


class MedicationCatalogResponse(BaseModel):
    id: int
    name: str
    active_ingredient: str | None = None
    strength: str | None = None
    dosage_form: str | None = None
    manufacturer: str | None = None
    description: str | None = None
    source: str | None = None

    model_config = ConfigDict(from_attributes=True)


class MedicationMemberResponse(BaseModel):
    id: int
    full_name: str
    relationship_label: str | None = None

    model_config = ConfigDict(from_attributes=True)


class MedicationMemberListResponse(BaseModel):
    items: list[MedicationMemberResponse]


class MedicationMemberLinkRequest(BaseModel):
    member_id: int = Field(gt=0)


class MedicationCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    active_ingredient: str | None = Field(default=None, max_length=200)
    strength: str | None = Field(default=None, max_length=100)
    dosage_form: DosageForm | None = None
    manufacturer: str | None = Field(default=None, max_length=200)
    description: str | None = None
    quantity: float = Field(default=0.0, ge=0.0)
    unit: MedicationUnit
    expiration_date: date | None = None
    opened_at: date | None = None
    low_stock_threshold: float | None = Field(default=None, ge=0.0)
    notes: str | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return _strip_non_empty(value, "name")

    @field_validator("active_ingredient", "strength", "manufacturer")
    @classmethod
    def validate_optional_strings(cls, value: str | None) -> str | None:
        return _strip_optional(value)


class MedicationUpdateRequest(BaseModel):
    quantity: float | None = Field(default=None, ge=0.0)
    unit: MedicationUnit | None = None
    expiration_date: date | None = None
    opened_at: date | None = None
    low_stock_threshold: float | None = Field(default=None, ge=0.0)
    notes: str | None = None

    model_config = ConfigDict(extra="forbid")


class InventoryUpdateRequest(BaseModel):
    quantity: float = Field(ge=0.0)
    low_stock_threshold: float | None = Field(default=None, ge=0.0)

    model_config = ConfigDict(extra="forbid")


class MedicationResponse(BaseModel):
    id: int
    family_id: int
    catalog: MedicationCatalogResponse
    quantity: float
    unit: str
    expiration_date: date | None = None
    opened_at: date | None = None
    low_stock_threshold: float | None = None
    status: str
    notes: str | None = None
    members: list[MedicationMemberResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def is_expired(self) -> bool:
        if self.expiration_date is None:
            return False
        return self.expiration_date < date.today()

    @computed_field
    @property
    def days_until_expiry(self) -> int | None:
        if self.expiration_date is None:
            return None
        return (self.expiration_date - date.today()).days

    @computed_field
    @property
    def is_low_stock(self) -> bool:
        if self.low_stock_threshold is None:
            return False
        return self.quantity <= self.low_stock_threshold

    @classmethod
    def from_model(cls, medication: Any) -> "MedicationResponse":
        links = getattr(medication, "member_links", None) or []
        members = [
            MedicationMemberResponse.model_validate(link.member)
            for link in links
            if getattr(link, "member", None) is not None
        ]
        # Compute dynamic status if not ARCHIVED
        effective_status = medication.status
        if effective_status != MedicationStatus.ARCHIVED.value:
            if medication.quantity <= 0:
                effective_status = MedicationStatus.DEPLETED.value
            elif (
                medication.expiration_date is not None
                and medication.expiration_date < date.today()
            ):
                effective_status = MedicationStatus.EXPIRED.value
            else:
                effective_status = MedicationStatus.ACTIVE.value

        return cls(
            id=medication.id,
            family_id=medication.family_id,
            catalog=MedicationCatalogResponse.model_validate(medication.catalog),
            quantity=medication.quantity,
            unit=medication.unit,
            expiration_date=medication.expiration_date,
            opened_at=medication.opened_at,
            low_stock_threshold=medication.low_stock_threshold,
            status=effective_status,
            notes=medication.notes,
            members=members,
            created_at=medication.created_at,
            updated_at=medication.updated_at,
        )


class MedicationListResponse(BaseModel):
    items: list[MedicationResponse]
