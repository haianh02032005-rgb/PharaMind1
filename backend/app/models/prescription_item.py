from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base

if TYPE_CHECKING:
    from backend.app.models.family_medication import FamilyMedication
    from backend.app.models.prescription import Prescription


class PrescriptionItem(Base):
    __tablename__ = "prescription_items"

    __table_args__ = (
        UniqueConstraint(
            "prescription_id",
            "family_medication_id",
            name="uq_prescription_item_medication",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    prescription_id: Mapped[int] = mapped_column(
        ForeignKey(
            "prescriptions.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    family_medication_id: Mapped[int] = mapped_column(
        ForeignKey(
            "family_medications.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    dose_amount: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    dose_unit: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    frequency_per_day: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    frequency_text: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    route: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    instructions: Mapped[str | None] = mapped_column(
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

    prescription: Mapped["Prescription"] = relationship(
        "Prescription",
        back_populates="items",
    )

    family_medication: Mapped["FamilyMedication"] = relationship(
        "FamilyMedication",
        lazy="joined",
    )

