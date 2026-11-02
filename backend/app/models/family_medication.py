from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Date,
    DateTime,
    Float,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base
from backend.app.modules.medications.enums import MedicationStatus

if TYPE_CHECKING:
    from backend.app.models.medication_catalog import MedicationCatalog
    from backend.app.models.member_medication import MemberMedication


class FamilyMedication(Base):
    __tablename__ = "family_medications"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    family_id: Mapped[int] = mapped_column(
        ForeignKey(
            "families.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    catalog_id: Mapped[int] = mapped_column(
        ForeignKey(
            "medication_catalogs.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    quantity: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )

    unit: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    expiration_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        index=True,
    )

    opened_at: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    low_stock_threshold: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default=MedicationStatus.ACTIVE.value,
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

    catalog: Mapped["MedicationCatalog"] = relationship(
        "MedicationCatalog",
        lazy="joined",
    )

    member_links: Mapped[list["MemberMedication"]] = relationship(
        "MemberMedication",
        back_populates="family_medication",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

