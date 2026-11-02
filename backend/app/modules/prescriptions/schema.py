from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from backend.app.modules.prescriptions.enums import (
    DoseUnit,
    MedicationRoute,
    PrescriptionStatus,
)


def _strip_optional(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


class PrescriptionMemberSummary(BaseModel):
    id: int
    full_name: str
    relationship_label: str | None = None

    model_config = ConfigDict(from_attributes=True)


class PrescriptionMedicationSummary(BaseModel):
    id: int
    name: str
    active_ingredient: str | None = None
    strength: str | None = None
    dosage_form: str | None = None
    unit: str


class PrescriptionItemCreateRequest(BaseModel):
    family_medication_id: int = Field(gt=0)
    dose_amount: float | None = Field(default=None, gt=0.0)
    dose_unit: DoseUnit | None = None
    frequency_per_day: float | None = Field(default=None, gt=0.0)
    frequency_text: str | None = Field(default=None, max_length=150)
    route: MedicationRoute | None = None
    instructions: str | None = None

    @field_validator("frequency_text", "instructions")
    @classmethod
    def validate_optional_text(cls, value: str | None) -> str | None:
        return _strip_optional(value)


class PrescriptionItemUpdateRequest(BaseModel):
    dose_amount: float | None = Field(default=None, gt=0.0)
    dose_unit: DoseUnit | None = None
    frequency_per_day: float | None = Field(default=None, gt=0.0)
    frequency_text: str | None = Field(default=None, max_length=150)
    route: MedicationRoute | None = None
    instructions: str | None = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("frequency_text", "instructions")
    @classmethod
    def validate_optional_text(cls, value: str | None) -> str | None:
        return _strip_optional(value)


class PrescriptionItemResponse(BaseModel):
    id: int
    prescription_id: int
    family_medication_id: int
    medication: PrescriptionMedicationSummary
    dose_amount: float | None = None
    dose_unit: str | None = None
    frequency_per_day: float | None = None
    frequency_text: str | None = None
    route: str | None = None
    instructions: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_model(cls, item: Any) -> "PrescriptionItemResponse":
        fam_med = item.family_medication
        catalog = fam_med.catalog
        return cls(
            id=item.id,
            prescription_id=item.prescription_id,
            family_medication_id=item.family_medication_id,
            medication=PrescriptionMedicationSummary(
                id=fam_med.id,
                name=catalog.name,
                active_ingredient=catalog.active_ingredient,
                strength=catalog.strength,
                dosage_form=catalog.dosage_form,
                unit=fam_med.unit,
            ),
            dose_amount=item.dose_amount,
            dose_unit=item.dose_unit,
            frequency_per_day=item.frequency_per_day,
            frequency_text=item.frequency_text,
            route=item.route,
            instructions=item.instructions,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )


class PrescriptionCreateRequest(BaseModel):
    member_id: int = Field(gt=0)
    title: str | None = Field(default=None, max_length=200)
    doctor_name: str | None = Field(default=None, max_length=150)
    facility_name: str | None = Field(default=None, max_length=200)
    issued_at: date | None = None
    start_date: date | None = None
    end_date: date | None = None
    status: PrescriptionStatus = PrescriptionStatus.ACTIVE
    notes: str | None = None

    @field_validator("title", "doctor_name", "facility_name", "notes")
    @classmethod
    def validate_optional_strings(cls, value: str | None) -> str | None:
        return _strip_optional(value)

    @model_validator(mode="after")
    def validate_date_range(self) -> "PrescriptionCreateRequest":
        if (
            self.start_date is not None
            and self.end_date is not None
            and self.start_date > self.end_date
        ):
            raise ValueError("start_date cannot be after end_date")
        return self


class PrescriptionUpdateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    doctor_name: str | None = Field(default=None, max_length=150)
    facility_name: str | None = Field(default=None, max_length=200)
    issued_at: date | None = None
    start_date: date | None = None
    end_date: date | None = None
    status: PrescriptionStatus | None = None
    notes: str | None = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("title", "doctor_name", "facility_name", "notes")
    @classmethod
    def validate_optional_strings(cls, value: str | None) -> str | None:
        return _strip_optional(value)

    @model_validator(mode="after")
    def validate_date_range(self) -> "PrescriptionUpdateRequest":
        if (
            self.start_date is not None
            and self.end_date is not None
            and self.start_date > self.end_date
        ):
            raise ValueError("start_date cannot be after end_date")
        return self


class PrescriptionResponse(BaseModel):
    id: int
    family_id: int
    member_id: int
    member: PrescriptionMemberSummary
    title: str | None = None
    doctor_name: str | None = None
    facility_name: str | None = None
    issued_at: date | None = None
    start_date: date | None = None
    end_date: date | None = None
    status: str
    notes: str | None = None
    items: list[PrescriptionItemResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_model(cls, prescription: Any) -> "PrescriptionResponse":
        raw_items = getattr(prescription, "items", None) or []
        return cls(
            id=prescription.id,
            family_id=prescription.family_id,
            member_id=prescription.member_id,
            member=PrescriptionMemberSummary.model_validate(
                prescription.member
            ),
            title=prescription.title,
            doctor_name=prescription.doctor_name,
            facility_name=prescription.facility_name,
            issued_at=prescription.issued_at,
            start_date=prescription.start_date,
            end_date=prescription.end_date,
            status=prescription.status,
            notes=prescription.notes,
            items=[
                PrescriptionItemResponse.from_model(item)
                for item in raw_items
            ],
            created_at=prescription.created_at,
            updated_at=prescription.updated_at,
        )


class PrescriptionListResponse(BaseModel):
    items: list[PrescriptionResponse]
