from datetime import date, time
from typing import Any

from sqlalchemy import delete, or_, select
from sqlalchemy.orm import Session

from backend.app.models.medication_schedule import MedicationSchedule
from backend.app.models.prescription import Prescription
from backend.app.models.prescription_item import PrescriptionItem
from backend.app.models.schedule_time import ScheduleTime
from backend.app.modules.schedules.enums import ScheduleStatus


class ScheduleRepository:
    # ------------------------------------------------------------------
    # Scoped PrescriptionItem Lookup
    # ------------------------------------------------------------------

    def get_scoped_prescription_item(
        self,
        db: Session,
        *,
        family_id: int,
        item_id: int,
    ) -> PrescriptionItem | None:
        stmt = (
            select(PrescriptionItem)
            .join(
                Prescription,
                Prescription.id == PrescriptionItem.prescription_id,
            )
            .where(
                PrescriptionItem.id == item_id,
                Prescription.family_id == family_id,
            )
        )
        return db.scalar(stmt)

    # ------------------------------------------------------------------
    # MedicationSchedule Persistence
    # ------------------------------------------------------------------

    def create_schedule(
        self,
        db: Session,
        schedule: MedicationSchedule,
    ) -> MedicationSchedule:
        db.add(schedule)
        db.flush()
        return schedule

    def get_schedule(
        self,
        db: Session,
        *,
        family_id: int,
        schedule_id: int,
    ) -> MedicationSchedule | None:
        stmt = select(MedicationSchedule).where(
            MedicationSchedule.id == schedule_id,
            MedicationSchedule.family_id == family_id,
        )
        return db.scalar(stmt)

    def list_schedules(
        self,
        db: Session,
        *,
        family_id: int,
        member_id: int | None = None,
        status: str | None = None,
        target_date: date | None = None,
        medication_id: int | None = None,
        include_archived: bool = False,
    ) -> list[MedicationSchedule]:
        stmt = select(MedicationSchedule).where(
            MedicationSchedule.family_id == family_id
        )

        if member_id is not None:
            stmt = stmt.where(MedicationSchedule.member_id == member_id)

        if medication_id is not None:
            stmt = stmt.where(
                MedicationSchedule.family_medication_id == medication_id
            )

        if target_date is not None:
            stmt = stmt.where(
                MedicationSchedule.start_date <= target_date,
                or_(
                    MedicationSchedule.end_date.is_(None),
                    MedicationSchedule.end_date >= target_date,
                ),
            )

        if status is not None:
            stmt = stmt.where(MedicationSchedule.status == status)
        elif not include_archived:
            stmt = stmt.where(
                MedicationSchedule.status != ScheduleStatus.ARCHIVED.value
            )

        stmt = stmt.order_by(MedicationSchedule.id.asc())
        return list(db.scalars(stmt).unique().all())

    def update_schedule(
        self,
        db: Session,
        schedule: MedicationSchedule,
        **changes: Any,
    ) -> MedicationSchedule:
        for field_name, value in changes.items():
            setattr(schedule, field_name, value)
        db.add(schedule)
        db.flush()
        return schedule

    # ------------------------------------------------------------------
    # ScheduleTime Persistence
    # ------------------------------------------------------------------

    def create_schedule_times(
        self,
        db: Session,
        *,
        schedule_id: int,
        times_of_day: list[time],
    ) -> list[ScheduleTime]:
        created: list[ScheduleTime] = []
        for t in sorted(times_of_day):
            st = ScheduleTime(
                schedule_id=schedule_id,
                time_of_day=t,
            )
            db.add(st)
            created.append(st)
        db.flush()
        return created

    def replace_schedule_times(
        self,
        db: Session,
        *,
        schedule_id: int,
        times_of_day: list[time],
    ) -> list[ScheduleTime]:
        db.execute(
            delete(ScheduleTime).where(
                ScheduleTime.schedule_id == schedule_id
            )
        )
        db.flush()
        return self.create_schedule_times(
            db,
            schedule_id=schedule_id,
            times_of_day=times_of_day,
        )

    # ------------------------------------------------------------------
    # Status Transitions
    # ------------------------------------------------------------------

    def pause_schedule(
        self,
        db: Session,
        schedule: MedicationSchedule,
    ) -> MedicationSchedule:
        schedule.status = ScheduleStatus.PAUSED.value
        db.add(schedule)
        db.flush()
        return schedule

    def resume_schedule(
        self,
        db: Session,
        schedule: MedicationSchedule,
    ) -> MedicationSchedule:
        schedule.status = ScheduleStatus.ACTIVE.value
        db.add(schedule)
        db.flush()
        return schedule

    def complete_schedule(
        self,
        db: Session,
        schedule: MedicationSchedule,
    ) -> MedicationSchedule:
        schedule.status = ScheduleStatus.COMPLETED.value
        db.add(schedule)
        db.flush()
        return schedule

    def archive_schedule(
        self,
        db: Session,
        schedule: MedicationSchedule,
    ) -> MedicationSchedule:
        schedule.status = ScheduleStatus.ARCHIVED.value
        db.add(schedule)
        db.flush()
        return schedule

    def restore_schedule(
        self,
        db: Session,
        schedule: MedicationSchedule,
    ) -> MedicationSchedule:
        schedule.status = ScheduleStatus.PAUSED.value
        db.add(schedule)
        db.flush()
        return schedule

    # ------------------------------------------------------------------
    # Daily & Next-Dose Queries
    # ------------------------------------------------------------------

    def get_daily_schedule(
        self,
        db: Session,
        *,
        family_id: int,
        member_id: int,
        target_date: date,
    ) -> list[MedicationSchedule]:
        stmt = (
            select(MedicationSchedule)
            .where(
                MedicationSchedule.family_id == family_id,
                MedicationSchedule.member_id == member_id,
                MedicationSchedule.status == ScheduleStatus.ACTIVE.value,
                MedicationSchedule.start_date <= target_date,
                or_(
                    MedicationSchedule.end_date.is_(None),
                    MedicationSchedule.end_date >= target_date,
                ),
            )
            .order_by(MedicationSchedule.id.asc())
        )
        return list(db.scalars(stmt).unique().all())

    def get_next_dose(
        self,
        db: Session,
        *,
        family_id: int,
        member_id: int,
        from_date: date,
    ) -> list[MedicationSchedule]:
        stmt = (
            select(MedicationSchedule)
            .where(
                MedicationSchedule.family_id == family_id,
                MedicationSchedule.member_id == member_id,
                MedicationSchedule.status == ScheduleStatus.ACTIVE.value,
                or_(
                    MedicationSchedule.end_date.is_(None),
                    MedicationSchedule.end_date >= from_date,
                ),
            )
            .order_by(MedicationSchedule.id.asc())
        )
        return list(db.scalars(stmt).unique().all())
