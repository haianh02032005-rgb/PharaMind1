from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import delete

from backend.app.db.session import SessionLocal
from backend.app.main import app
from backend.app.models.family import Family
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


def _cleanup(user_ids: list[int], family_ids: list[int]) -> None:
    with SessionLocal() as session:
        if family_ids:
            session.execute(delete(Family).where(Family.id.in_(family_ids)))
        if user_ids:
            session.execute(delete(User).where(User.id.in_(user_ids)))
        session.commit()


def test_allergy_profile_crud_and_source_preserved():
    """TASK 05 §18–20, §39–41, §65, §75: Create, list, update, delete allergies."""
    owner_id, _, token = _create_user_and_token("alg_owner")
    family_ids: list[int] = []

    try:
        fam_id = client.post(
            "/families",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Gia đình Dị Ứng"},
        ).json()["id"]
        family_ids.append(fam_id)

        mem_id = client.post(
            f"/families/{fam_id}/members",
            headers={"Authorization": f"Bearer {token}"},
            json={"full_name": "Bà Lan"},
        ).json()["id"]

        create_res = client.post(
            f"/families/{fam_id}/members/{mem_id}/allergies",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "allergen": "Penicillin",
                "allergy_type": "DRUG",
                "severity": "SEVERE",
                "reaction_description": "Nổi mề đay, khó thở",
                "recorded_at": "2019-06-15",
                "source": "Người dùng khai báo",
                "notes": "Tuyệt đối tránh nhóm beta-lactam",
            },
        )
        assert create_res.status_code == 201
        alg = create_res.json()
        alg_id = alg["id"]
        assert alg["allergen"] == "Penicillin"
        assert alg["allergy_type"] == "DRUG"
        assert alg["severity"] == "SEVERE"
        assert alg["source"] == "Người dùng khai báo"

        list_res = client.get(
            f"/families/{fam_id}/members/{mem_id}/allergies",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert list_res.status_code == 200
        items = list_res.json()["items"]
        assert len(items) == 1
        assert items[0]["allergen"] == "Penicillin"

        upd_res = client.patch(
            f"/families/{fam_id}/members/{mem_id}/allergies/{alg_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"severity": "MODERATE", "source": "Bệnh viện Bạch Mai"},
        )
        assert upd_res.status_code == 200
        assert upd_res.json()["severity"] == "MODERATE"
        assert upd_res.json()["source"] == "Bệnh viện Bạch Mai"

        del_res = client.delete(
            f"/families/{fam_id}/members/{mem_id}/allergies/{alg_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert del_res.status_code == 204
    finally:
        _cleanup([owner_id], family_ids)
