from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base

if TYPE_CHECKING:
    from backend.app.models.import_session import ImportSession


class ImportItem(Base):
    """A single staged row (medication / candidate) inside an import session (§26.2)."""

    __tablename__ = "import_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    import_session_id: Mapped[int] = mapped_column(
        ForeignKey("import_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    row_index: Mapped[int] = mapped_column(Integer, nullable=False)
    item_type: Mapped[str] = mapped_column(String(40), nullable=False)
    raw_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    normalized_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    edited_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    resolution_status: Mapped[str] = mapped_column(String(30), nullable=False)
    matched_entity_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    matched_entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    session: Mapped["ImportSession"] = relationship("ImportSession", back_populates="items")
