from datetime import date, datetime

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base
from backend.app.shared.enums import AllergyType, Severity


class AllergyProfile(Base):
    __tablename__ = "allergy_profiles"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    member_id: Mapped[int] = mapped_column(
        ForeignKey(
            "family_members.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    allergen: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    allergy_type: Mapped[str] = mapped_column(
        String(30),
        default=AllergyType.OTHER.value,
        nullable=False,
    )

    severity: Mapped[str] = mapped_column(
        String(30),
        default=Severity.UNKNOWN.value,
        nullable=False,
    )

    reaction_description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    recorded_at: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    source: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
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

