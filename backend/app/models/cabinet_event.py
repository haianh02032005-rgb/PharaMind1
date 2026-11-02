from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    JSON,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base

if TYPE_CHECKING:
    from backend.app.models.compartment import Compartment


class CabinetEvent(Base):
    __tablename__ = "cabinet_events"

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

    cabinet_id: Mapped[int] = mapped_column(
        ForeignKey(
            "cabinets.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    compartment_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "compartments.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    source: Mapped[str] = mapped_column(
        String(30),
        default="SIMULATOR",
        nullable=False,
    )

    payload: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    compartment: Mapped["Compartment | None"] = relationship(
        "Compartment",
        lazy="joined",
    )

