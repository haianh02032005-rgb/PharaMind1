from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base

if TYPE_CHECKING:
    from backend.app.models.family_medication import FamilyMedication
    from backend.app.models.family_member import FamilyMember
    from backend.app.models.prescription_item import PrescriptionItem
    from backend.app.models.schedule_time import ScheduleTime


class MedicationSchedule(Base):
    __tablename__ = "medication_schedules"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    family_id: Mapped[int] = mapped_column(
        ForeignKey("families.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    member_id: Mapped[int] = mapped_column(
        ForeignKey("family_members.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    prescription_item_id: Mapped[int] = mapped_column(
        ForeignKey("prescription_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    family_medication_id: Mapped[int] = mapped_column(
        ForeignKey("family_medications.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    recurrence_type: Mapped[str] = mapped_column(
        String(30),
        default="DAILY",
        nullable=False,
    )

    recurrence_config: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    end_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    reminder_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    reminder_before_minutes: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    grace_period_minutes: Mapped[int] = mapped_column(
        Integer,
        default=30,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="ACTIVE",
        nullable=False,
        index=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    member: Mapped["FamilyMember"] = relationship(
        "FamilyMember",
        lazy="joined",
    )

    prescription_item: Mapped["PrescriptionItem"] = relationship(
        "PrescriptionItem",
        lazy="joined",
    )

    family_medication: Mapped["FamilyMedication"] = relationship(
        "FamilyMedication",
        lazy="joined",
    )

    schedule_times: Mapped[list["ScheduleTime"]] = relationship(
        "ScheduleTime",
        back_populates="schedule",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="ScheduleTime.time_of_day.asc()",
    )

