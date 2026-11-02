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


def test_medical_condition_crud_and_member_isolation():
    """TASK 05 §16, §17, §37, §38, §64: Create, list, update, delete medical conditions with member scope."""
    owner_id, _, token = _create_user_and_token("cond_owner")
    family_ids: list[int] = []

    try:
        fam_id = client.post(
            "/families",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Gia đình Bệnh Lý"},
        ).json()["id"]
        family_ids.append(fam_id)

        mem_1 = client.post(
            f"/families/{fam_id}/members",
            headers={"Authorization": f"Bearer {token}"},
            json={"full_name": "Bà Lan"},
        ).json()["id"]

        mem_2 = client.post(
            f"/families/{fam_id}/members",
            headers={"Authorization": f"Bearer {token}"},
            json={"full_name": "Ông Minh"},
        ).json()["id"]

        # Create condition for mem_1
        create_res = client.post(
            f"/families/{fam_id}/members/{mem_1}/conditions",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "Tăng huyết áp",
                "diagnosed_at": "2020-03-01",
                "status": "ACTIVE",
                "notes": "Theo dõi huyết áp mỗi ngày",
            },
        )
        assert create_res.status_code == 201
        cond_data = create_res.json()
        cond_id = cond_data["id"]
        assert cond_data["name"] == "Tăng huyết áp"
        assert cond_data["status"] == "ACTIVE"

        # List conditions for mem_1
        list_res = client.get(
            f"/families/{fam_id}/members/{mem_1}/conditions",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert list_res.status_code == 200
        assert len(list_res.json()["items"]) == 1

        # Cross-member IDOR check: mem_2 cannot update/delete mem_1's condition
        idor_upd = client.patch(
            f"/families/{fam_id}/members/{mem_2}/conditions/{cond_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"status": "RESOLVED"},
        )
        assert idor_upd.status_code == 404

        # Update condition on mem_1
        upd_res = client.patch(
            f"/families/{fam_id}/members/{mem_1}/conditions/{cond_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"status": "RESOLVED", "notes": "Đã ổn định hơn"},
        )
        assert upd_res.status_code == 200
        assert upd_res.json()["status"] == "RESOLVED"
        assert upd_res.json()["notes"] == "Đã ổn định hơn"

        # Delete condition on mem_1
        del_res = client.delete(
            f"/families/{fam_id}/members/{mem_1}/conditions/{cond_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert del_res.status_code == 204

        after_del = client.get(
            f"/families/{fam_id}/members/{mem_1}/conditions",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert after_del.json()["items"] == []
    finally:
        _cleanup([owner_id], family_ids)
