from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base

if TYPE_CHECKING:
    from backend.app.models.import_session import ImportSession


class ImportEntityLink(Base):
    """Provenance record linking an import session to created/updated domain entities (§26.4)."""

    __tablename__ = "import_entity_links"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    import_session_id: Mapped[int] = mapped_column(
        ForeignKey("import_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    previous_snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    new_snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    session: Mapped["ImportSession"] = relationship(
        "ImportSession", back_populates="entity_links"
    )
