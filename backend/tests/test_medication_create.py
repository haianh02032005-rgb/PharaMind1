from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from backend.app.db.session import SessionLocal
from backend.app.main import app
from backend.app.models.family import Family
from backend.app.models.family_medication import FamilyMedication
from backend.app.models.medication_catalog import MedicationCatalog
from backend.app.models.user import User


client = TestClient(app)


def _create_user_and_token(label: str) -> tuple[int, str, str]:
    email = f"{label}_{uuid4().hex[:10]}@example.com"
    password = "StrongPass123"
    reg = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": f"User {label}",
        },
    )
    assert reg.status_code == 201
    login = client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    assert login.status_code == 200
    return reg.json()["id"], email, login.json()["access_token"]


def _cleanup(
    user_ids: list[int],
    family_ids: list[int],
    catalog_ids: list[int] | None = None,
) -> None:
    with SessionLocal() as session:
        if family_ids:
            session.execute(delete(Family).where(Family.id.in_(family_ids)))
        if catalog_ids:
            session.execute(
                delete(MedicationCatalog).where(
                    MedicationCatalog.id.in_(catalog_ids)
                )
            )
        if user_ids:
            session.execute(delete(User).where(User.id.in_(user_ids)))
        session.commit()


def test_create_medication_and_catalog_reuse():
    """TASK 06 §22–27, §64, §65: Creating medication creates catalog + family medication and reuses matching catalog."""
    user_a_id, _, token_a = _create_user_and_token("med_create_a")
    user_b_id, _, token_b = _create_user_and_token("med_create_b")
    family_ids: list[int] = []
    catalog_ids: list[int] = []
    unique_suffix = uuid4().hex[:6]

    try:
        fam_a = client.post(
            "/families",
            headers={"Authorization": f"Bearer {token_a}"},
            json={"name": "Gia đình A"},
        ).json()["id"]
        family_ids.append(fam_a)

        fam_b = client.post(
            "/families",
            headers={"Authorization": f"Bearer {token_b}"},
            json={"name": "Gia đình B"},
        ).json()["id"]
        family_ids.append(fam_b)

        drug_name = f"Amlodipine-{unique_suffix}"
        res_a = client.post(
            f"/families/{fam_a}/medications",
            headers={"Authorization": f"Bearer {token_a}"},
            json={
                "name": f"  {drug_name}  ",
                "active_ingredient": "Amlodipine",
                "strength": "5 mg",
                "dosage_form": "TABLET",
                "manufacturer": "Example Pharma",
                "quantity": 30,
                "unit": "TABLET",
                "expiration_date": "2027-05-31",
                "low_stock_threshold": 5,
                "notes": "Thuốc huyết áp",
            },
        )
        assert res_a.status_code == 201
        med_a = res_a.json()
        assert med_a["family_id"] == fam_a
        assert med_a["catalog"]["name"] == drug_name
        assert med_a["catalog"]["active_ingredient"] == "Amlodipine"
        assert med_a["catalog"]["strength"] == "5 mg"
        assert med_a["catalog"]["dosage_form"] == "TABLET"
        assert med_a["quantity"] == 30
        assert med_a["unit"] == "TABLET"
        assert med_a["status"] == "ACTIVE"
        assert med_a["is_expired"] is False
        assert med_a["is_low_stock"] is False

        cat_id = med_a["catalog"]["id"]
        catalog_ids.append(cat_id)

        # Family B creates the exact same medication identity -> reuses catalog, creates separate FamilyMedication
        res_b = client.post(
            f"/families/{fam_b}/medications",
            headers={"Authorization": f"Bearer {token_b}"},
            json={
                "name": drug_name.lower(),
                "active_ingredient": "amlodipine",
                "strength": "5 mg",
                "dosage_form": "TABLET",
                "manufacturer": "example pharma",
                "quantity": 15,
                "unit": "TABLET",
            },
        )
        assert res_b.status_code == 201
        med_b = res_b.json()
        assert med_b["catalog"]["id"] == cat_id
        assert med_b["id"] != med_a["id"]
        assert med_b["family_id"] == fam_b
        assert med_b["quantity"] == 15

        with SessionLocal() as session:
            db_meds = list(
                session.scalars(
                    select(FamilyMedication).where(
                        FamilyMedication.catalog_id == cat_id
                    )
                ).all()
            )
            assert len(db_meds) == 2
    finally:
        _cleanup([user_a_id, user_b_id], family_ids, catalog_ids)

