from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class CuratedPharmacy(Base):
    __tablename__ = "curated_pharmacies"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    area: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    address: Mapped[str] = mapped_column(String(300), nullable=False)
    phone: Mapped[str] = mapped_column(String(30), nullable=False)
    phone_kind: Mapped[str] = mapped_column(String(30), nullable=False)
    source_url: Mapped[str] = mapped_column(String(500), nullable=False)
