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


def test_update_medication_and_forbid_family_id_change():
    """TASK 06 §32, §33: Update medication fields and reject family_id modification."""
    owner_id, _, token = _create_user_and_token("med_upd_owner")
    family_ids: list[int] = []
    catalog_ids: list[int] = []

    try:
        fam_id = client.post(
            "/families",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Gia đình Cập Nhật Thuốc"},
        ).json()["id"]
        family_ids.append(fam_id)

        med = client.post(
            f"/families/{fam_id}/medications",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": f"VitaminC-{uuid4().hex[:6]}",
                "quantity": 20,
                "unit": "TABLET",
            },
        ).json()
        med_id = med["id"]
        catalog_ids.append(med["catalog"]["id"])

        upd_res = client.patch(
            f"/families/{fam_id}/medications/{med_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "quantity": 15,
                "opened_at": "2026-01-10",
                "low_stock_threshold": 5,
                "notes": "Đã mở nắp",
            },
        )
        assert upd_res.status_code == 200
        upd_data = upd_res.json()
        assert upd_data["quantity"] == 15
        assert upd_data["opened_at"] == "2026-01-10"
        assert upd_data["low_stock_threshold"] == 5
        assert upd_data["notes"] == "Đã mở nắp"

        # Attempting to patch family_id is forbidden (422)
        forbid_res = client.patch(
            f"/families/{fam_id}/medications/{med_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"family_id": 999},
        )
        assert forbid_res.status_code == 422
    finally:
        _cleanup([owner_id], family_ids, catalog_ids)

