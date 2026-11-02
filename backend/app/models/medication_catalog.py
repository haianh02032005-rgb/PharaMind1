from datetime import datetime

from sqlalchemy import (
    DateTime,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base
from backend.app.modules.medications.enums import MedicationSource


class MedicationCatalog(Base):
    __tablename__ = "medication_catalogs"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
    )

    active_ingredient: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        index=True,
    )

    strength: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    dosage_form: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    manufacturer: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    source: Mapped[str | None] = mapped_column(
        String(100),
        default=MedicationSource.USER_ENTERED.value,
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

