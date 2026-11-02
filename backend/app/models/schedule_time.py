from datetime import datetime, time
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Time,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base

if TYPE_CHECKING:
    from backend.app.models.medication_schedule import MedicationSchedule


class ScheduleTime(Base):
    __tablename__ = "schedule_times"

    __table_args__ = (
        UniqueConstraint(
            "schedule_id",
            "time_of_day",
            name="uq_schedule_time",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    schedule_id: Mapped[int] = mapped_column(
        ForeignKey("medication_schedules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    time_of_day: Mapped[time] = mapped_column(
        Time,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    schedule: Mapped["MedicationSchedule"] = relationship(
        "MedicationSchedule",
        back_populates="schedule_times",
    )

