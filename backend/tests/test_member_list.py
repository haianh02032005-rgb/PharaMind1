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


def test_list_members_scoped_to_family_and_include_archived():
    """TASK 05 §31, §34, §70: List members only returns current family's members and filters archived."""
    user_a_id, _, token_a = _create_user_and_token("list_mem_a")
    user_b_id, _, token_b = _create_user_and_token("list_mem_b")
    family_ids: list[int] = []

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

        mem_a1 = client.post(
            f"/families/{fam_a}/members",
            headers={"Authorization": f"Bearer {token_a}"},
            json={
                "full_name": "Bà Nguyễn Thị Lan",
                "relationship_label": "Grandmother",
                "gender": "FEMALE",
            },
        ).json()["id"]

        mem_a2 = client.post(
            f"/families/{fam_a}/members",
            headers={"Authorization": f"Bearer {token_a}"},
            json={
                "full_name": "Ông Nguyễn Văn Minh",
                "relationship_label": "Grandfather",
                "gender": "MALE",
            },
        ).json()["id"]

        client.post(
            f"/families/{fam_b}/members",
            headers={"Authorization": f"Bearer {token_b}"},
            json={
                "full_name": "Thành Viên Nhà B",
                "relationship_label": "Father",
            },
        )

        # Archive mem_a2
        arch_res = client.post(
            f"/families/{fam_a}/members/{mem_a2}/archive",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert arch_res.status_code == 200
        assert arch_res.json()["status"] == "ARCHIVED"

        # Default list_members only includes ACTIVE members of Family A
        active_list = client.get(
            f"/families/{fam_a}/members",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert active_list.status_code == 200
        active_items = active_list.json()["items"]
        assert len(active_items) == 1
        assert active_items[0]["id"] == mem_a1
        assert active_items[0]["full_name"] == "Bà Nguyễn Thị Lan"

        # include_archived=true returns both ACTIVE and ARCHIVED of Family A
        all_list = client.get(
            f"/families/{fam_a}/members?include_archived=true",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert all_list.status_code == 200
        all_ids = [item["id"] for item in all_list.json()["items"]]
        assert all_ids == [mem_a1, mem_a2]

        # Restore mem_a2
        rest_res = client.post(
            f"/families/{fam_a}/members/{mem_a2}/restore",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert rest_res.status_code == 200
        assert rest_res.json()["status"] == "ACTIVE"

        restored_list = client.get(
            f"/families/{fam_a}/members",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert len(restored_list.json()["items"]) == 2
    finally:
        _cleanup([user_a_id, user_b_id], family_ids)

