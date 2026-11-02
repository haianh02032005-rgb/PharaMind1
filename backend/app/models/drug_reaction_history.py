from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base
from backend.app.shared.enums import Severity


class DrugReactionHistory(Base):
    __tablename__ = "drug_reaction_histories"

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

    drug_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    active_ingredient: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    reaction: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    severity: Mapped[str] = mapped_column(
        String(30),
        default=Severity.UNKNOWN.value,
        nullable=False,
    )

    occurred_at: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    confirmed_by_professional: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
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

