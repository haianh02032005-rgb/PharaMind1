from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base

if TYPE_CHECKING:
    from backend.app.models.family_member import FamilyMember
    from backend.app.models.family_medication import FamilyMedication


class MemberMedication(Base):
    __tablename__ = "member_medications"

    __table_args__ = (
        UniqueConstraint(
            "member_id",
            "family_medication_id",
            name="uq_member_medication",
        ),
    )

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

    family_medication_id: Mapped[int] = mapped_column(
        ForeignKey(
            "family_medications.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    member: Mapped["FamilyMember"] = relationship(
        "FamilyMember",
        lazy="joined",
    )

    family_medication: Mapped["FamilyMedication"] = relationship(
        "FamilyMedication",
        back_populates="member_links",
    )

