import datetime as dt
from datetime import date, datetime, time
import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from backend.app.modules.schedules.enums import RecurrenceType


_TIME_PATTERN = re.compile(r"^(\d{2}):(\d{2})$")


def _strip_optional(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def parse_time_str(raw: str) -> time:
    if not isinstance(raw, str):
        raise ValueError("Time must be a string in HH:MM format")
    cleaned = raw.strip()
    match = _TIME_PATTERN.match(cleaned)
    if not match:
        raise ValueError(f"Invalid time format '{raw}', expected HH:MM (00:00 to 23:59)")
    hour = int(match.group(1))
    minute = int(match.group(2))
    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        raise ValueError(f"Invalid time '{raw}', must be between 00:00 and 23:59")
    return time(hour=hour, minute=minute)


def format_time_obj(t: time) -> str:
    return f"{t.hour:02d}:{t.minute:02d}"


def validate_and_normalize_times(times: list[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for raw in times:
        parsed = parse_time_str(raw)
        formatted = format_time_obj(parsed)
        if formatted in seen:
            raise ValueError(f"Duplicate schedule time '{formatted}' is not allowed")
        seen.add(formatted)
        normalized.append(formatted)
    return sorted(normalized)


class ScheduleMemberSummary(BaseModel):
    id: int
    full_name: str
    relationship_label: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ScheduleMedicationSummary(BaseModel):
    id: int
    name: str
    active_ingredient: str | None = None
    strength: str | None = None
    dosage_form: str | None = None
    unit: str


class ScheduleTimeResponse(BaseModel):
    id: int
    schedule_id: int
    time_of_day: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_model(cls, st: Any) -> "ScheduleTimeResponse":
        return cls(
            id=st.id,
            schedule_id=st.schedule_id,
            time_of_day=format_time_obj(st.time_of_day),
            created_at=st.created_at,
        )


class MedicationScheduleCreateRequest(BaseModel):
    prescription_item_id: int = Field(gt=0)
    start_date: date
    end_date: date | None = None
    recurrence_type: RecurrenceType = RecurrenceType.DAILY
    recurrence_config: dict[str, Any] | None = None
    times: list[str] = Field(default_factory=list)
    reminder_enabled: bool = True
    reminder_before_minutes: int = Field(default=0, ge=0)
    grace_period_minutes: int = Field(default=30, ge=0)
    notes: str | None = None

    @field_validator("notes")
    @classmethod
    def validate_optional_notes(cls, value: str | None) -> str | None:
        return _strip_optional(value)

    @field_validator("times")
    @classmethod
    def validate_times_list(cls, value: list[str]) -> list[str]:
        return validate_and_normalize_times(value)

    @model_validator(mode="after")
    def validate_schedule_constraints(self) -> "MedicationScheduleCreateRequest":
        if (
            self.end_date is not None
            and self.start_date > self.end_date
        ):
            raise ValueError("start_date cannot be after end_date")
        if self.recurrence_type != RecurrenceType.PRN and len(self.times) == 0:
            raise ValueError("times cannot be empty for non-PRN schedule")
        return self


class MedicationScheduleUpdateRequest(BaseModel):
    start_date: date | None = None
    end_date: date | None = None
    recurrence_type: RecurrenceType | None = None
    recurrence_config: dict[str, Any] | None = None
    times: list[str] | None = None
    reminder_enabled: bool | None = None
    reminder_before_minutes: int | None = Field(default=None, ge=0)
    grace_period_minutes: int | None = Field(default=None, ge=0)
    notes: str | None = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("notes")
    @classmethod
    def validate_optional_notes(cls, value: str | None) -> str | None:
        return _strip_optional(value)

    @field_validator("times")
    @classmethod
    def validate_times_list(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        return validate_and_normalize_times(value)

    @model_validator(mode="after")
    def validate_date_range(self) -> "MedicationScheduleUpdateRequest":
        if (
            self.start_date is not None
            and self.end_date is not None
            and self.start_date > self.end_date
        ):
            raise ValueError("start_date cannot be after end_date")
        return self


class MedicationScheduleResponse(BaseModel):
    id: int
    family_id: int
    member_id: int
    prescription_item_id: int
    family_medication_id: int
    member: ScheduleMemberSummary
    medication: ScheduleMedicationSummary
    dose_amount: float | None = None
    dose_unit: str | None = None
    recurrence_type: str
    recurrence_config: dict[str, Any] | None = None
    start_date: date
    end_date: date | None = None
    times: list[str] = Field(default_factory=list)
    schedule_times: list[ScheduleTimeResponse] = Field(default_factory=list)
    reminder_enabled: bool
    reminder_before_minutes: int
    grace_period_minutes: int
    status: str
    notes: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_model(cls, schedule: Any) -> "MedicationScheduleResponse":
        fam_med = schedule.family_medication
        catalog = fam_med.catalog
        item = schedule.prescription_item
        raw_times = sorted(
            getattr(schedule, "schedule_times", None) or [],
            key=lambda st: st.time_of_day,
        )
        return cls(
            id=schedule.id,
            family_id=schedule.family_id,
            member_id=schedule.member_id,
            prescription_item_id=schedule.prescription_item_id,
            family_medication_id=schedule.family_medication_id,
            member=ScheduleMemberSummary.model_validate(schedule.member),
            medication=ScheduleMedicationSummary(
                id=fam_med.id,
                name=catalog.name,
                active_ingredient=catalog.active_ingredient,
                strength=catalog.strength,
                dosage_form=catalog.dosage_form,
                unit=fam_med.unit,
            ),
            dose_amount=item.dose_amount if item is not None else None,
            dose_unit=item.dose_unit if item is not None else None,
            recurrence_type=schedule.recurrence_type,
            recurrence_config=schedule.recurrence_config,
            start_date=schedule.start_date,
            end_date=schedule.end_date,
            times=[format_time_obj(st.time_of_day) for st in raw_times],
            schedule_times=[
                ScheduleTimeResponse.from_model(st) for st in raw_times
            ],
            reminder_enabled=schedule.reminder_enabled,
            reminder_before_minutes=schedule.reminder_before_minutes,
            grace_period_minutes=schedule.grace_period_minutes,
            status=schedule.status,
            notes=schedule.notes,
            created_at=schedule.created_at,
            updated_at=schedule.updated_at,
        )


class MedicationScheduleListResponse(BaseModel):
    items: list[MedicationScheduleResponse]


class DailyScheduleItem(BaseModel):
    schedule_id: int
    time: str
    medication: ScheduleMedicationSummary
    dose_amount: float | None = None
    dose_unit: str | None = None
    status: str = "SCHEDULED"


class DailyScheduleResponse(BaseModel):
    date: dt.date
    items: list[DailyScheduleItem] = Field(default_factory=list)


class NextDoseResponse(BaseModel):
    schedule_id: int | None = None
    date: dt.date | None = None
    time: str | None = None
    medication: ScheduleMedicationSummary | None = None
    dose_amount: float | None = None
    dose_unit: str | None = None
