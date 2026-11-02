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


def test_primary_emergency_contact_exclusivity_and_crud():
    """TASK 05 §23, §44, §45, §67, §77: Setting a new primary contact unsets existing primary contact."""
    owner_id, _, token = _create_user_and_token("ec_owner")
    family_ids: list[int] = []

    try:
        fam_id = client.post(
            "/families",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Gia đình Liên Hệ Khẩn Cấp"},
        ).json()["id"]
        family_ids.append(fam_id)

        mem_id = client.post(
            f"/families/{fam_id}/members",
            headers={"Authorization": f"Bearer {token}"},
            json={"full_name": "Bà Lan"},
        ).json()["id"]

        # Create Contact A as primary
        res_a = client.post(
            f"/families/{fam_id}/members/{mem_id}/emergency-contacts",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "Nguyễn Văn A",
                "relationship": "Con trai",
                "phone": "+84901234567",
                "is_primary": True,
            },
        )
        assert res_a.status_code == 201
        contact_a_id = res_a.json()["id"]
        assert res_a.json()["is_primary"] is True

        # Create Contact B as primary -> Contact A must become is_primary=False
        res_b = client.post(
            f"/families/{fam_id}/members/{mem_id}/emergency-contacts",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "Nguyễn Thị B",
                "relationship": "Con gái",
                "phone": "0912345678",
                "is_primary": True,
            },
        )
        assert res_b.status_code == 201
        contact_b_id = res_b.json()["id"]
        assert res_b.json()["is_primary"] is True

        list_res = client.get(
            f"/families/{fam_id}/members/{mem_id}/emergency-contacts",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert list_res.status_code == 200
        by_id = {c["id"]: c for c in list_res.json()["items"]}
        assert by_id[contact_a_id]["is_primary"] is False
        assert by_id[contact_b_id]["is_primary"] is True

        # PATCH Contact A back to is_primary=True -> Contact B becomes False
        patch_a = client.patch(
            f"/families/{fam_id}/members/{mem_id}/emergency-contacts/{contact_a_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"is_primary": True},
        )
        assert patch_a.status_code == 200
        assert patch_a.json()["is_primary"] is True

        list_after_patch = client.get(
            f"/families/{fam_id}/members/{mem_id}/emergency-contacts",
            headers={"Authorization": f"Bearer {token}"},
        )
        by_id_after = {c["id"]: c for c in list_after_patch.json()["items"]}
        assert by_id_after[contact_a_id]["is_primary"] is True
        assert by_id_after[contact_b_id]["is_primary"] is False

        # Delete Contact B
        del_b = client.delete(
            f"/families/{fam_id}/members/{mem_id}/emergency-contacts/{contact_b_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert del_b.status_code == 204
    finally:
        _cleanup([owner_id], family_ids)

