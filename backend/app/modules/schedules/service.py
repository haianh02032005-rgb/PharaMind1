from datetime import date, datetime, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.models.family import Family
from backend.app.models.family_medication import FamilyMedication
from backend.app.models.family_member import FamilyMember
from backend.app.models.family_membership import FamilyMembership
from backend.app.models.medication_schedule import MedicationSchedule
from backend.app.models.prescription import Prescription
from backend.app.models.prescription_item import PrescriptionItem
from backend.app.modules.families.exceptions import (
    FamilyArchivedError,
    InsufficientFamilyPermissionError,
)
from backend.app.modules.medications.enums import MedicationStatus
from backend.app.modules.medications.exceptions import (
    MedicationArchivedError,
    MedicationNotFoundError,
)
from backend.app.modules.medications.repository import MedicationRepository
from backend.app.modules.members.exceptions import (
    MemberArchivedError,
    MemberNotFoundError,
)
from backend.app.modules.members.repository import MemberRepository
from backend.app.modules.prescriptions.enums import PrescriptionStatus
from backend.app.modules.prescriptions.exceptions import (
    PrescriptionArchivedError,
    PrescriptionCompletedError,
    PrescriptionItemNotFoundError,
)
from backend.app.modules.schedules.enums import (
    RecurrenceType,
    ScheduleStatus,
)
from backend.app.modules.schedules.exceptions import (
    InvalidScheduleDateRangeError,
    InvalidScheduleTimesError,
    MedicationExpiredError,
    ScheduleArchivedError,
    ScheduleCompletedError,
    ScheduleFrequencyMismatchError,
    ScheduleInvalidStatusTransitionError,
    ScheduleNotFoundError,
)
from backend.app.modules.schedules.repository import ScheduleRepository
from backend.app.modules.schedules.schema import (
    DailyScheduleItem,
    DailyScheduleResponse,
    MedicationScheduleCreateRequest,
    MedicationScheduleListResponse,
    MedicationScheduleResponse,
    MedicationScheduleUpdateRequest,
    NextDoseResponse,
    ScheduleMedicationSummary,
    format_time_obj,
    parse_time_str,
)
from backend.app.shared.enums import FamilyRole, FamilyStatus, MemberStatus


WRITE_SCHEDULE_ROLES = (
    FamilyRole.OWNER,
    FamilyRole.ADMIN,
    FamilyRole.CAREGIVER,
)

ADMIN_SCHEDULE_ROLES = (
    FamilyRole.OWNER,
    FamilyRole.ADMIN,
)


class ScheduleService:
    def __init__(
        self,
        repository: ScheduleRepository | None = None,
        member_repository: MemberRepository | None = None,
        medication_repository: MedicationRepository | None = None,
    ) -> None:
        self.repository = repository or ScheduleRepository()
        self.member_repository = member_repository or MemberRepository()
        self.medication_repository = (
            medication_repository or MedicationRepository()
        )

    # ------------------------------------------------------------------
    # CRUD & Lifecycle Operations
    # ------------------------------------------------------------------

    def create_schedule(
        self,
        db: Session,
        membership: FamilyMembership,
        payload: MedicationScheduleCreateRequest,
    ) -> MedicationScheduleResponse:
        self._ensure_roles(membership, *WRITE_SCHEDULE_ROLES)
        self._ensure_family_active(membership.family)

        item = self.repository.get_scoped_prescription_item(
            db,
            family_id=membership.family_id,
            item_id=payload.prescription_item_id,
        )
        if item is None:
            raise PrescriptionItemNotFoundError("Prescription item not found")

        prescription = item.prescription
        self._ensure_prescription_valid_for_schedule(prescription)

        # Derive Member from Prescription (§16, §44)
        member = self._get_scoped_member(db, membership, prescription.member_id)
        self._ensure_member_active(member)

        # Derive FamilyMedication from PrescriptionItem (§16, §45)
        medication = self._get_scoped_medication(
            db, membership, item.family_medication_id
        )
        self._ensure_medication_valid_for_schedule(medication)

        # Date range & Prescription date bounds (§20, §21, §63–65)
        self._validate_dates_against_prescription(
            start_date=payload.start_date,
            end_date=payload.end_date,
            prescription=prescription,
        )

        # Frequency consistency check (§18, §60, §66)
        self._validate_frequency_and_times(
            recurrence_type=payload.recurrence_type.value,
            times=payload.times,
            item=item,
        )

        schedule = MedicationSchedule(
            family_id=membership.family_id,
            member_id=member.id,
            prescription_item_id=item.id,
            family_medication_id=medication.id,
            recurrence_type=payload.recurrence_type.value,
            recurrence_config=payload.recurrence_config,
            start_date=payload.start_date,
            end_date=payload.end_date,
            reminder_enabled=payload.reminder_enabled,
            reminder_before_minutes=payload.reminder_before_minutes,
            grace_period_minutes=payload.grace_period_minutes,
            status=ScheduleStatus.ACTIVE.value,
            notes=payload.notes,
        )
        created = self.repository.create_schedule(db, schedule)

        parsed_times = [parse_time_str(t) for t in payload.times]
        if parsed_times:
            self.repository.create_schedule_times(
                db,
                schedule_id=created.id,
                times_of_day=parsed_times,
            )

        db.commit()
        db.refresh(created)
        return MedicationScheduleResponse.from_model(created)

    def list_schedules(
        self,
        db: Session,
        membership: FamilyMembership,
        *,
        member_id: int | None = None,
        status: ScheduleStatus | None = None,
        target_date: date | None = None,
        medication_id: int | None = None,
        include_archived: bool = False,
    ) -> MedicationScheduleListResponse:
        if member_id is not None:
            self._get_scoped_member(db, membership, member_id)
        if medication_id is not None:
            self._get_scoped_medication(db, membership, medication_id)

        rows = self.repository.list_schedules(
            db,
            family_id=membership.family_id,
            member_id=member_id,
            status=status.value if status is not None else None,
            target_date=target_date,
            medication_id=medication_id,
            include_archived=include_archived,
        )
        return MedicationScheduleListResponse(
            items=[MedicationScheduleResponse.from_model(row) for row in rows]
        )

    def list_member_schedules(
        self,
        db: Session,
        membership: FamilyMembership,
        member_id: int,
        *,
        status: ScheduleStatus | None = None,
        include_archived: bool = False,
    ) -> MedicationScheduleListResponse:
        member = self._get_scoped_member(db, membership, member_id)
        rows = self.repository.list_schedules(
            db,
            family_id=membership.family_id,
            member_id=member.id,
            status=status.value if status is not None else None,
            include_archived=include_archived,
        )
        return MedicationScheduleListResponse(
            items=[MedicationScheduleResponse.from_model(row) for row in rows]
        )

    def get_schedule_detail(
        self,
        db: Session,
        membership: FamilyMembership,
        schedule_id: int,
    ) -> MedicationScheduleResponse:
        schedule = self._get_scoped_schedule(db, membership, schedule_id)
        return MedicationScheduleResponse.from_model(schedule)

    def update_schedule(
        self,
        db: Session,
        membership: FamilyMembership,
        schedule_id: int,
        payload: MedicationScheduleUpdateRequest,
    ) -> MedicationScheduleResponse:
        self._ensure_roles(membership, *WRITE_SCHEDULE_ROLES)
        self._ensure_family_active(membership.family)

        schedule = self._get_scoped_schedule(db, membership, schedule_id)
        self._ensure_schedule_editable(schedule)

        changes: dict[str, Any] = {}
        times_updated = False
        new_times_str: list[str] | None = None

        for field_name in payload.model_fields_set:
            value = getattr(payload, field_name)
            if field_name == "times":
                times_updated = True
                new_times_str = value
                continue
            if field_name == "recurrence_type" and value is not None:
                value = value.value
            changes[field_name] = value

        effective_start = changes.get("start_date", schedule.start_date)
        effective_end = changes.get("end_date", schedule.end_date)
        if effective_start is None:
            raise InvalidScheduleDateRangeError("start_date cannot be null")

        item = schedule.prescription_item
        prescription = item.prescription
        self._validate_dates_against_prescription(
            start_date=effective_start,
            end_date=effective_end,
            prescription=prescription,
        )

        effective_recurrence = changes.get(
            "recurrence_type", schedule.recurrence_type
        )
        if effective_recurrence is None:
            raise InvalidScheduleTimesError("recurrence_type cannot be null")

        if times_updated:
            if new_times_str is None:
                raise InvalidScheduleTimesError("times cannot be null")
            effective_times = new_times_str
        else:
            effective_times = [
                format_time_obj(st.time_of_day)
                for st in schedule.schedule_times
            ]

        if times_updated or "recurrence_type" in changes:
            self._validate_frequency_and_times(
                recurrence_type=effective_recurrence,
                times=effective_times,
                item=item,
            )

        if changes:
            schedule = self.repository.update_schedule(db, schedule, **changes)

        if times_updated and new_times_str is not None:
            parsed_times = [parse_time_str(t) for t in new_times_str]
            self.repository.replace_schedule_times(
                db,
                schedule_id=schedule.id,
                times_of_day=parsed_times,
            )

        db.commit()
        db.refresh(schedule)
        return MedicationScheduleResponse.from_model(schedule)

    def pause_schedule(
        self,
        db: Session,
        membership: FamilyMembership,
        schedule_id: int,
    ) -> MedicationScheduleResponse:
        self._ensure_roles(membership, *WRITE_SCHEDULE_ROLES)
        self._ensure_family_active(membership.family)

        schedule = self._get_scoped_schedule(db, membership, schedule_id)
        self._ensure_schedule_editable(schedule)

        updated = self.repository.pause_schedule(db, schedule)
        db.commit()
        db.refresh(updated)
        return MedicationScheduleResponse.from_model(updated)

    def resume_schedule(
        self,
        db: Session,
        membership: FamilyMembership,
        schedule_id: int,
    ) -> MedicationScheduleResponse:
        self._ensure_roles(membership, *WRITE_SCHEDULE_ROLES)
        self._ensure_family_active(membership.family)

        schedule = self._get_scoped_schedule(db, membership, schedule_id)
        self._ensure_schedule_editable(schedule)

        today = self._current_local_datetime().date()
        if schedule.end_date is not None and schedule.end_date < today:
            raise ScheduleInvalidStatusTransitionError(
                "Cannot resume schedule after its end_date has passed"
            )

        updated = self.repository.resume_schedule(db, schedule)
        db.commit()
        db.refresh(updated)
        return MedicationScheduleResponse.from_model(updated)

    def complete_schedule(
        self,
        db: Session,
        membership: FamilyMembership,
        schedule_id: int,
    ) -> MedicationScheduleResponse:
        self._ensure_roles(membership, *WRITE_SCHEDULE_ROLES)
        self._ensure_family_active(membership.family)

        schedule = self._get_scoped_schedule(db, membership, schedule_id)
        if schedule.status == ScheduleStatus.ARCHIVED.value:
            raise ScheduleArchivedError("Schedule is archived")

        updated = self.repository.complete_schedule(db, schedule)
        db.commit()
        db.refresh(updated)
        return MedicationScheduleResponse.from_model(updated)

    def archive_schedule(
        self,
        db: Session,
        membership: FamilyMembership,
        schedule_id: int,
    ) -> MedicationScheduleResponse:
        self._ensure_roles(membership, *ADMIN_SCHEDULE_ROLES)
        self._ensure_family_active(membership.family)

        schedule = self._get_scoped_schedule(db, membership, schedule_id)
        updated = self.repository.archive_schedule(db, schedule)
        db.commit()
        db.refresh(updated)
        return MedicationScheduleResponse.from_model(updated)

    def restore_schedule(
        self,
        db: Session,
        membership: FamilyMembership,
        schedule_id: int,
    ) -> MedicationScheduleResponse:
        self._ensure_roles(membership, *ADMIN_SCHEDULE_ROLES)
        self._ensure_family_active(membership.family)

        schedule = self._get_scoped_schedule(db, membership, schedule_id)
        updated = self.repository.restore_schedule(db, schedule)
        db.commit()
        db.refresh(updated)
        return MedicationScheduleResponse.from_model(updated)

    # ------------------------------------------------------------------
    # Daily Timeline & Next Dose
    # ------------------------------------------------------------------

    def get_daily_schedule(
        self,
        db: Session,
        membership: FamilyMembership,
        member_id: int,
        *,
        target_date: date | None = None,
    ) -> DailyScheduleResponse:
        member = self._get_scoped_member(db, membership, member_id)
        effective_date = (
            target_date
            if target_date is not None
            else self._current_local_datetime().date()
        )

        schedules = self.repository.get_daily_schedule(
            db,
            family_id=membership.family_id,
            member_id=member.id,
            target_date=effective_date,
        )

        occurrences: list[tuple[time, int, DailyScheduleItem]] = []
        for schedule in schedules:
            if not self._schedule_matches_date(schedule, effective_date):
                continue
            fam_med = schedule.family_medication
            catalog = fam_med.catalog
            item = schedule.prescription_item
            med_summary = ScheduleMedicationSummary(
                id=fam_med.id,
                name=catalog.name,
                active_ingredient=catalog.active_ingredient,
                strength=catalog.strength,
                dosage_form=catalog.dosage_form,
                unit=fam_med.unit,
            )
            for st in schedule.schedule_times:
                daily_item = DailyScheduleItem(
                    schedule_id=schedule.id,
                    time=format_time_obj(st.time_of_day),
                    medication=med_summary,
                    dose_amount=item.dose_amount if item is not None else None,
                    dose_unit=item.dose_unit if item is not None else None,
                    status="SCHEDULED",
                )
                occurrences.append((st.time_of_day, schedule.id, daily_item))

        occurrences.sort(key=lambda entry: (entry[0], entry[1]))
        return DailyScheduleResponse(
            date=effective_date,
            items=[entry[2] for entry in occurrences],
        )

    def get_next_dose(
        self,
        db: Session,
        membership: FamilyMembership,
        member_id: int,
        *,
        now: datetime | None = None,
    ) -> NextDoseResponse:
        member = self._get_scoped_member(db, membership, member_id)
        ref_now = self._normalize_local_datetime(now)
        today = ref_now.date()
        current_time = ref_now.timetz().replace(tzinfo=None)

        schedules = self.repository.get_next_dose(
            db,
            family_id=membership.family_id,
            member_id=member.id,
            from_date=today,
        )
        if not schedules:
            return NextDoseResponse()

        min_start = min(s.start_date for s in schedules)
        scan_start = max(today, min_start)

        for offset in range(0, 367):
            candidate_date = scan_start + timedelta(days=offset)
            day_candidates: list[tuple[time, int, MedicationSchedule]] = []

            for schedule in schedules:
                if not self._schedule_matches_date(schedule, candidate_date):
                    continue
                for st in schedule.schedule_times:
                    if (
                        candidate_date == today
                        and st.time_of_day <= current_time
                    ):
                        continue
                    day_candidates.append(
                        (st.time_of_day, schedule.id, schedule)
                    )

            if day_candidates:
                day_candidates.sort(key=lambda entry: (entry[0], entry[1]))
                best_time, _, best_schedule = day_candidates[0]
                fam_med = best_schedule.family_medication
                catalog = fam_med.catalog
                item = best_schedule.prescription_item
                return NextDoseResponse(
                    schedule_id=best_schedule.id,
                    date=candidate_date,
                    time=format_time_obj(best_time),
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
                )

        return NextDoseResponse()

    # ------------------------------------------------------------------
    # Recurrence & Timezone Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _current_local_datetime() -> datetime:
        tz = ZoneInfo(settings.default_timezone)
        return datetime.now(tz)

    @classmethod
    def _normalize_local_datetime(cls, value: datetime | None) -> datetime:
        tz = ZoneInfo(settings.default_timezone)
        if value is None:
            return datetime.now(tz)
        if value.tzinfo is None:
            return value.replace(tzinfo=tz)
        return value.astimezone(tz)

    @staticmethod
    def _schedule_matches_date(
        schedule: MedicationSchedule,
        target_date: date,
    ) -> bool:
        if schedule.status != ScheduleStatus.ACTIVE.value:
            return False
        if target_date < schedule.start_date:
            return False
        if schedule.end_date is not None and target_date > schedule.end_date:
            return False
        if not schedule.schedule_times:
            return False

        rec_type = schedule.recurrence_type
        if rec_type == RecurrenceType.PRN.value:
            return False
        if rec_type == RecurrenceType.DAILY.value:
            return True
        if rec_type == RecurrenceType.WEEKLY.value:
            config = schedule.recurrence_config or {}
            days = config.get("days_of_week")
            if isinstance(days, list) and days:
                day_name = target_date.strftime("%A").upper()
                return day_name in {str(d).upper() for d in days}
            return True
        if rec_type == RecurrenceType.CUSTOM.value:
            config = schedule.recurrence_config or {}
            interval = config.get("interval_days")
            if isinstance(interval, int) and interval > 0:
                delta_days = (target_date - schedule.start_date).days
                return delta_days >= 0 and (delta_days % interval == 0)
            return True
        return True

    # ------------------------------------------------------------------
    # Internal Validation & Guards
    # ------------------------------------------------------------------

    def _get_scoped_schedule(
        self,
        db: Session,
        membership: FamilyMembership,
        schedule_id: int,
    ) -> MedicationSchedule:
        schedule = self.repository.get_schedule(
            db,
            family_id=membership.family_id,
            schedule_id=schedule_id,
        )
        if schedule is None:
            raise ScheduleNotFoundError("Schedule not found")
        return schedule

    def _get_scoped_member(
        self,
        db: Session,
        membership: FamilyMembership,
        member_id: int,
    ) -> FamilyMember:
        member = self.member_repository.get_member(
            db,
            family_id=membership.family_id,
            member_id=member_id,
        )
        if member is None:
            raise MemberNotFoundError("Member not found")
        return member

    def _get_scoped_medication(
        self,
        db: Session,
        membership: FamilyMembership,
        medication_id: int,
    ) -> FamilyMedication:
        medication = self.medication_repository.get_family_medication(
            db,
            family_id=membership.family_id,
            medication_id=medication_id,
        )
        if medication is None:
            raise MedicationNotFoundError("Medication not found")
        return medication

    @staticmethod
    def _ensure_roles(
        membership: FamilyMembership,
        *allowed_roles: FamilyRole,
    ) -> None:
        allowed_values = {role.value for role in allowed_roles}
        if membership.role not in allowed_values:
            raise InsufficientFamilyPermissionError(
                "Insufficient family permission"
            )

    @staticmethod
    def _ensure_family_active(family: Family) -> None:
        if family.status != FamilyStatus.ACTIVE.value:
            raise FamilyArchivedError("Family archived")

    @staticmethod
    def _ensure_member_active(member: FamilyMember) -> None:
        if member.status != MemberStatus.ACTIVE.value:
            raise MemberArchivedError("Member archived")

    @classmethod
    def _ensure_medication_valid_for_schedule(
        cls,
        medication: FamilyMedication,
    ) -> None:
        if medication.status == MedicationStatus.ARCHIVED.value:
            raise MedicationArchivedError("Medication archived")
        today = cls._current_local_datetime().date()
        if medication.status == MedicationStatus.EXPIRED.value or (
            medication.expiration_date is not None
            and medication.expiration_date < today
        ):
            raise MedicationExpiredError(
                "Cannot create schedule for expired medication"
            )

    @staticmethod
    def _ensure_prescription_valid_for_schedule(
        prescription: Prescription,
    ) -> None:
        if prescription.status == PrescriptionStatus.ARCHIVED.value:
            raise PrescriptionArchivedError("Prescription is archived")
        if prescription.status == PrescriptionStatus.COMPLETED.value:
            raise PrescriptionCompletedError(
                "Cannot create schedule from a completed prescription"
            )

    @staticmethod
    def _ensure_schedule_editable(schedule: MedicationSchedule) -> None:
        if schedule.status == ScheduleStatus.ARCHIVED.value:
            raise ScheduleArchivedError("Schedule is archived")
        if schedule.status == ScheduleStatus.COMPLETED.value:
            raise ScheduleCompletedError(
                "Completed schedule cannot be modified"
            )

    @staticmethod
    def _validate_dates_against_prescription(
        *,
        start_date: date,
        end_date: date | None,
        prescription: Prescription,
    ) -> None:
        if end_date is not None and start_date > end_date:
            raise InvalidScheduleDateRangeError(
                "start_date cannot be after end_date"
            )
        if (
            prescription.start_date is not None
            and start_date < prescription.start_date
        ):
            raise InvalidScheduleDateRangeError(
                "Schedule start_date cannot be before prescription start_date"
            )
        if prescription.end_date is not None:
            if start_date > prescription.end_date:
                raise InvalidScheduleDateRangeError(
                    "Schedule start_date cannot be after prescription end_date"
                )
            if end_date is not None and end_date > prescription.end_date:
                raise InvalidScheduleDateRangeError(
                    "Schedule end_date cannot be after prescription end_date"
                )

    @staticmethod
    def _validate_frequency_and_times(
        *,
        recurrence_type: str,
        times: list[str],
        item: PrescriptionItem,
    ) -> None:
        if recurrence_type == RecurrenceType.PRN.value:
            return

        if len(times) == 0:
            raise InvalidScheduleTimesError(
                "times cannot be empty for non-PRN schedule"
            )

        if (
            recurrence_type == RecurrenceType.DAILY.value
            and item.frequency_per_day is not None
            and item.frequency_per_day.is_integer()
        ):
            expected_count = int(item.frequency_per_day)
            if len(times) != expected_count:
                raise ScheduleFrequencyMismatchError(
                    "Schedule time count does not match prescription frequency"
                )
