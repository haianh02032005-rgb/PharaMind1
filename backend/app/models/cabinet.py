from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base

if TYPE_CHECKING:
    from backend.app.models.compartment import Compartment


class Cabinet(Base):
    __tablename__ = "cabinets"

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

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    device_code: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="OFFLINE",
        nullable=False,
        index=True,
    )

    hardware_mode: Mapped[str] = mapped_column(
        String(30),
        default="SIMULATOR",
        nullable=False,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    last_seen_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
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

    compartments: Mapped[list["Compartment"]] = relationship(
        "Compartment",
        back_populates="cabinet",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="Compartment.position.asc()",
    )

