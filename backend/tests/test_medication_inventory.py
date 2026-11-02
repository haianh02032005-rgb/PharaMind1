from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import delete

from backend.app.db.session import SessionLocal
from backend.app.main import app
from backend.app.models.family import Family
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
    catalog_ids: list[int],
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


def test_inventory_validation_zero_depleted_expired_and_low_stock():
    """TASK 06 §36–41, §58, §66–68: Negative quantity rejected (422), 0 -> DEPLETED, expired -> EXPIRED, low stock."""
    owner_id, _, token = _create_user_and_token("med_inv_owner")
    family_ids: list[int] = []
    catalog_ids: list[int] = []

    try:
        fam_id = client.post(
            "/families",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Gia đình Tồn Kho"},
        ).json()["id"]
        family_ids.append(fam_id)

        # Negative quantity rejected on create
        bad_create = client.post(
            f"/families/{fam_id}/medications",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "BadMed",
                "quantity": -5,
                "unit": "TABLET",
            },
        )
        assert bad_create.status_code == 422

        # Create normal medication with low_stock_threshold = 5
        med = client.post(
            f"/families/{fam_id}/medications",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": f"Losartan-{uuid4().hex[:6]}",
                "quantity": 10,
                "unit": "TABLET",
                "low_stock_threshold": 5,
            },
        ).json()
        med_id = med["id"]
        catalog_ids.append(med["catalog"]["id"])
        assert med["is_low_stock"] is False

        # Negative quantity rejected on inventory patch
        bad_inv = client.patch(
            f"/families/{fam_id}/medications/{med_id}/inventory",
            headers={"Authorization": f"Bearer {token}"},
            json={"quantity": -5},
        )
        assert bad_inv.status_code == 422

        # Update inventory to 5 -> low stock = True, status = ACTIVE
        low_res = client.patch(
            f"/families/{fam_id}/medications/{med_id}/inventory",
            headers={"Authorization": f"Bearer {token}"},
            json={"quantity": 5},
        )
        assert low_res.status_code == 200
        assert low_res.json()["is_low_stock"] is True
        assert low_res.json()["status"] == "ACTIVE"

        # Update inventory to 0 -> status = DEPLETED
        zero_res = client.patch(
            f"/families/{fam_id}/medications/{med_id}/inventory",
            headers={"Authorization": f"Bearer {token}"},
            json={"quantity": 0},
        )
        assert zero_res.status_code == 200
        assert zero_res.json()["status"] == "DEPLETED"

        # Create expired medication (2020-01-01) -> is_expired = True, status = EXPIRED
        exp_med = client.post(
            f"/families/{fam_id}/medications",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": f"OldDrug-{uuid4().hex[:6]}",
                "quantity": 12,
                "unit": "TABLET",
                "expiration_date": "2020-01-01",
            },
        )
        assert exp_med.status_code == 201
        exp_data = exp_med.json()
        catalog_ids.append(exp_data["catalog"]["id"])
        assert exp_data["is_expired"] is True
        assert exp_data["status"] == "EXPIRED"
        assert exp_data["days_until_expiry"] < 0
    finally:
        _cleanup([owner_id], family_ids, catalog_ids)

