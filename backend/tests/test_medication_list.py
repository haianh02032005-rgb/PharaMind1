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


def test_list_and_search_medications_with_archived_filtering():
    """TASK 06 §28–30, §76: List family medications, search by name/ingredient/manufacturer, and filter archived."""
    user_a_id, _, token_a = _create_user_and_token("med_list_a")
    user_b_id, _, token_b = _create_user_and_token("med_list_b")
    family_ids: list[int] = []
    catalog_ids: list[int] = []
    suffix = uuid4().hex[:6]

    try:
        fam_a = client.post(
            "/families",
            headers={"Authorization": f"Bearer {token_a}"},
            json={"name": "Family A"},
        ).json()["id"]
        family_ids.append(fam_a)

        fam_b = client.post(
            "/families",
            headers={"Authorization": f"Bearer {token_b}"},
            json={"name": "Family B"},
        ).json()["id"]
        family_ids.append(fam_b)

        m1 = client.post(
            f"/families/{fam_a}/medications",
            headers={"Authorization": f"Bearer {token_a}"},
            json={
                "name": f"Amlodipine-{suffix}",
                "active_ingredient": "Amlodipine besylate",
                "manufacturer": "Pfizer",
                "quantity": 20,
                "unit": "TABLET",
            },
        ).json()
        catalog_ids.append(m1["catalog"]["id"])

        m2 = client.post(
            f"/families/{fam_a}/medications",
            headers={"Authorization": f"Bearer {token_a}"},
            json={
                "name": f"Panadol-{suffix}",
                "active_ingredient": "Paracetamol",
                "manufacturer": "GSK",
                "quantity": 10,
                "unit": "TABLET",
            },
        ).json()
        catalog_ids.append(m2["catalog"]["id"])

        mb = client.post(
            f"/families/{fam_b}/medications",
            headers={"Authorization": f"Bearer {token_b}"},
            json={
                "name": f"Metformin-{suffix}",
                "active_ingredient": "Metformin",
                "quantity": 50,
                "unit": "TABLET",
            },
        ).json()
        catalog_ids.append(mb["catalog"]["id"])

        # Search in Family A for "amlodipine"
        search_res = client.get(
            f"/families/{fam_a}/medications?search=amlodipine",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert search_res.status_code == 200
        search_items = search_res.json()["items"]
        assert len(search_items) == 1
        assert search_items[0]["id"] == m1["id"]

        # Archive m2
        client.post(
            f"/families/{fam_a}/medications/{m2['id']}/archive",
            headers={"Authorization": f"Bearer {token_a}"},
        )

        # Default list excludes ARCHIVED
        default_list = client.get(
            f"/families/{fam_a}/medications",
            headers={"Authorization": f"Bearer {token_a}"},
        ).json()["items"]
        assert [item["id"] for item in default_list] == [m1["id"]]

        # include_archived=true returns both m1 and m2
        all_list = client.get(
            f"/families/{fam_a}/medications?include_archived=true",
            headers={"Authorization": f"Bearer {token_a}"},
        ).json()["items"]
        assert [item["id"] for item in all_list] == [m1["id"], m2["id"]]
    finally:
        _cleanup([user_a_id, user_b_id], family_ids, catalog_ids)

