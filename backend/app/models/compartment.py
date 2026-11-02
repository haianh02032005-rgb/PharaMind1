from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base

if TYPE_CHECKING:
    from backend.app.models.cabinet import Cabinet
    from backend.app.models.family_medication import FamilyMedication


class Compartment(Base):
    __tablename__ = "compartments"

    __table_args__ = (
        UniqueConstraint(
            "cabinet_id",
            "position",
            name="uq_cabinet_compartment_position",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    cabinet_id: Mapped[int] = mapped_column(
        ForeignKey(
            "cabinets.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    position: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    label: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    family_medication_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "family_medications.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="EMPTY",
        nullable=False,
        index=True,
    )

    is_open: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
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

    cabinet: Mapped["Cabinet"] = relationship(
        "Cabinet",
        back_populates="compartments",
    )

    family_medication: Mapped["FamilyMedication | None"] = relationship(
        "FamilyMedication",
        lazy="joined",
    )

