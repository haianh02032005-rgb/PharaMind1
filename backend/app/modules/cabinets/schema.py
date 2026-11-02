import datetime as dt
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _strip_required(value: str, field_label: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{field_label} cannot be blank")
    return cleaned


def _strip_optional(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


class CabinetCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    device_code: str = Field(min_length=1, max_length=100)
    notes: str | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return _strip_required(value, "name")

    @field_validator("device_code")
    @classmethod
    def validate_device_code(cls, value: str) -> str:
        return _strip_required(value, "device_code")

    @field_validator("notes")
    @classmethod
    def validate_notes(cls, value: str | None) -> str | None:
        return _strip_optional(value)


class MedicationAssignmentRequest(BaseModel):
    family_medication_id: int = Field(gt=0)


class CompartmentMedicationSummary(BaseModel):
    id: int
    name: str
    active_ingredient: str | None = None
    strength: str | None = None
    dosage_form: str | None = None
    quantity: float
    unit: str
    expiration_date: dt.date | None = None
    status: str

    @classmethod
    def from_model(cls, fam_med: Any) -> "CompartmentMedicationSummary":
        catalog = fam_med.catalog
        return cls(
            id=fam_med.id,
            name=catalog.name,
            active_ingredient=catalog.active_ingredient,
            strength=catalog.strength,
            dosage_form=catalog.dosage_form,
            quantity=fam_med.quantity,
            unit=fam_med.unit,
            expiration_date=fam_med.expiration_date,
            status=fam_med.status,
        )


class CompartmentNextDoseMemberSummary(BaseModel):
    id: int
    full_name: str


class CompartmentNextDoseSummary(BaseModel):
    schedule_id: int
    date: dt.date
    time: str
    member: CompartmentNextDoseMemberSummary
    dose_amount: float | None = None
    dose_unit: str | None = None


class CompartmentResponse(BaseModel):
    id: int
    cabinet_id: int
    position: int
    object_id: str
    label: str | None = None
    status: str
    is_open: bool
    family_medication_id: int | None = None
    medication: CompartmentMedicationSummary | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_model(cls, comp: Any) -> "CompartmentResponse":
        fam_med = getattr(comp, "family_medication", None)
        return cls(
            id=comp.id,
            cabinet_id=comp.cabinet_id,
            position=comp.position,
            object_id=f"drawer_{comp.position:02d}",
            label=comp.label,
            status=comp.status,
            is_open=comp.is_open,
            family_medication_id=comp.family_medication_id,
            medication=(
                CompartmentMedicationSummary.from_model(fam_med)
                if fam_med is not None
                else None
            ),
            created_at=comp.created_at,
            updated_at=comp.updated_at,
        )


class CompartmentDetailResponse(CompartmentResponse):
    next_dose: CompartmentNextDoseSummary | None = None


class CompartmentListResponse(BaseModel):
    items: list[CompartmentResponse]


class CabinetResponse(BaseModel):
    id: int
    family_id: int
    name: str
    device_code: str
    status: str
    hardware_mode: str
    notes: str | None = None
    last_seen_at: datetime | None = None
    compartments: list[CompartmentResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_model(cls, cabinet: Any) -> "CabinetResponse":
        raw_comps = sorted(
            getattr(cabinet, "compartments", None) or [],
            key=lambda c: c.position,
        )
        return cls(
            id=cabinet.id,
            family_id=cabinet.family_id,
            name=cabinet.name,
            device_code=cabinet.device_code,
            status=cabinet.status,
            hardware_mode=cabinet.hardware_mode,
            notes=cabinet.notes,
            last_seen_at=cabinet.last_seen_at,
            compartments=[
                CompartmentResponse.from_model(c) for c in raw_comps
            ],
            created_at=cabinet.created_at,
            updated_at=cabinet.updated_at,
        )


class CabinetListResponse(BaseModel):
    items: list[CabinetResponse]


class CabinetCompartmentStateItem(BaseModel):
    id: int
    position: int
    object_id: str
    is_open: bool
    status: str
    family_medication_id: int | None = None


class CabinetStateResponse(BaseModel):
    cabinet_id: int
    status: str
    hardware_mode: str
    last_seen_at: datetime | None = None
    compartments: list[CabinetCompartmentStateItem] = Field(
        default_factory=list
    )


class CabinetEventResponse(BaseModel):
    id: int
    family_id: int
    cabinet_id: int
    compartment_id: int | None = None
    compartment_position: int | None = None
    event_type: str
    source: str
    payload: dict[str, Any] | None = None
    occurred_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_model(cls, evt: Any) -> "CabinetEventResponse":
        comp = getattr(evt, "compartment", None)
        pos = comp.position if comp is not None else None
        if pos is None and isinstance(evt.payload, dict):
            pos = evt.payload.get("position")
        return cls(
            id=evt.id,
            family_id=evt.family_id,
            cabinet_id=evt.cabinet_id,
            compartment_id=evt.compartment_id,
            compartment_position=pos,
            event_type=evt.event_type,
            source=evt.source,
            payload=evt.payload,
            occurred_at=evt.occurred_at,
        )


class CabinetEventListResponse(BaseModel):
    items: list[CabinetEventResponse]


# ------------------------------------------------------------------
# Digital Twin 3D Summary Schemas (TASK 10 §29–32, §53–56)
# ------------------------------------------------------------------


class DigitalTwinCabinetHeader(BaseModel):
    id: int
    name: str
    device_code: str
    status: str
    hardware_mode: str
    last_seen_at: datetime | None = None


class DigitalTwinScheduleBrief(BaseModel):
    schedule_id: int
    recurrence_type: str
    times: list[str] = Field(default_factory=list)
    dose_amount: float | None = None
    dose_unit: str | None = None
    instructions: str | None = None


class DigitalTwinMemberSummary(BaseModel):
    id: int
    full_name: str
    relationship_label: str | None = None
    schedules: list[DigitalTwinScheduleBrief] = Field(default_factory=list)
    next_schedule: str | None = None
    next_dose_date: dt.date | None = None
    next_dose_time: str | None = None
    next_dose_amount: float | None = None
    next_dose_unit: str | None = None


class DigitalTwinAllergyAlert(BaseModel):
    member_id: int
    member_name: str
    alert_type: str
    substance: str
    severity: str | None = None
    reaction: str | None = None
    message: str


class DigitalTwinCompartmentItem(BaseModel):
    id: int
    position: int
    object_id: str
    label: str | None = None
    status: str
    is_open: bool
    medication: CompartmentMedicationSummary | None = None
    members: list[DigitalTwinMemberSummary] = Field(default_factory=list)
    next_dose: CompartmentNextDoseSummary | None = None
    warnings: list[str] = Field(default_factory=list)
    allergy_alerts: list[DigitalTwinAllergyAlert] = Field(default_factory=list)


class DigitalTwinResponse(BaseModel):
    cabinet: DigitalTwinCabinetHeader
    next_dose_position: int | None = None
    next_dose: CompartmentNextDoseSummary | None = None
    compartments: list[DigitalTwinCompartmentItem] = Field(
        default_factory=list
    )


# ------------------------------------------------------------------
# Drawer Open Capsule Fly-out & Medication Info Reveal Schemas (§30)
# ------------------------------------------------------------------


class CompartmentRevealMemberItem(BaseModel):
    id: int
    full_name: str
    relationship_label: str | None = None
    dose_amount: float | None = None
    dose_unit: str | None = None
    next_schedule: str | None = None
    next_date: dt.date | None = None
    next_time: str | None = None
    times: list[str] = Field(default_factory=list)
    instructions: str | None = None


class CompartmentRevealWarningItem(BaseModel):
    type: str
    severity: str | None = None
    member_id: int | None = None
    member_name: str | None = None
    substance: str | None = None
    message: str


class CompartmentRevealResponse(BaseModel):
    cabinet_id: int
    cabinet_status: str
    position: int
    object_id: str
    label: str | None = None
    status: str
    is_open: bool
    is_next_dose: bool = False
    medication: CompartmentMedicationSummary | None = None
    members: list[CompartmentRevealMemberItem] = Field(default_factory=list)
    next_dose: CompartmentNextDoseSummary | None = None
    warnings: list[CompartmentRevealWarningItem] = Field(default_factory=list)
