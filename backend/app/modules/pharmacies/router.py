from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.api.dependencies import get_db
from backend.app.models.curated_pharmacy import CuratedPharmacy

router = APIRouter()


class CuratedPharmacyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    address: str
    phone: str
    phone_kind: str
    source_url: str


@router.get("/curated", response_model=list[CuratedPharmacyOut])
def list_curated_pharmacies(db: Session = Depends(get_db)):
    return db.scalars(
        select(CuratedPharmacy)
        .where(CuratedPharmacy.area == "haui-campus-1")
        .order_by(CuratedPharmacy.name)
    ).all()
