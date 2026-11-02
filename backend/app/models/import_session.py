from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base

if TYPE_CHECKING:
    from backend.app.models.import_entity_link import ImportEntityLink
    from backend.app.models.import_item import ImportItem
    from backend.app.models.import_validation_issue import ImportValidationIssue


class ImportSession(Base):
    """Staging session for an OCR/Excel prescription import (§26.1)."""

    __tablename__ = "import_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    family_id: Mapped[int] = mapped_column(
        ForeignKey("families.id", ondelete="CASCADE"), nullable=False, index=True
    )
    member_id: Mapped[int] = mapped_column(
        ForeignKey("family_members.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_type: Mapped[str] = mapped_column(String(30), nullable=False)
    source_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    source_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    storage_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    import_mode: Mapped[str] = mapped_column(String(50), nullable=False)
    overall_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    parser_version: Mapped[str] = mapped_column(String(30), nullable=False, default="1.0.0")
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    normalized_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    review_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    commit_summary: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    target_prescription_id: Mapped[int | None] = mapped_column(
        ForeignKey("prescriptions.id", ondelete="SET NULL"), nullable=True
    )
    is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    duplicate_of_import_id: Mapped[int | None] = mapped_column(
        ForeignKey("import_sessions.id", ondelete="SET NULL"), nullable=True
    )
    created_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    reviewed_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    committed_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    committed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    items: Mapped[list["ImportItem"]] = relationship(
        "ImportItem",
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="ImportItem.row_index.asc()",
    )
    validation_issues: Mapped[list["ImportValidationIssue"]] = relationship(
        "ImportValidationIssue",
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="ImportValidationIssue.id.asc()",
    )
    entity_links: Mapped[list["ImportEntityLink"]] = relationship(
        "ImportEntityLink",
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="ImportEntityLink.id.asc()",
    )
