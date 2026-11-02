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


def test_list_families_scoped_to_user_memberships():
    """TASK 04 §50: User A (OWNER of F1, CAREGIVER of F2), User B (OWNER of F2, F3)."""
    user_a_id, email_a, token_a = _create_user_and_token("list_a")
    user_b_id, _, token_b = _create_user_and_token("list_b")
    family_ids: list[int] = []

    try:
        f1 = client.post(
            "/families",
            headers={"Authorization": f"Bearer {token_a}"},
            json={"name": "Gia đình 1"},
        )
        assert f1.status_code == 201
        f1_id = f1.json()["id"]
        family_ids.append(f1_id)

        f2 = client.post(
            "/families",
            headers={"Authorization": f"Bearer {token_b}"},
            json={"name": "Gia đình 2"},
        )
        assert f2.status_code == 201
        f2_id = f2.json()["id"]
        family_ids.append(f2_id)

        f3 = client.post(
            "/families",
            headers={"Authorization": f"Bearer {token_b}"},
            json={"name": "Gia đình 3"},
        )
        assert f3.status_code == 201
        f3_id = f3.json()["id"]
        family_ids.append(f3_id)

        add_res = client.post(
            f"/families/{f2_id}/memberships",
            headers={"Authorization": f"Bearer {token_b}"},
            json={"email": email_a, "role": "CAREGIVER"},
        )
        assert add_res.status_code == 201

        list_a = client.get(
            "/families",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert list_a.status_code == 200
        items_a = {item["id"]: item for item in list_a.json()["items"]}

        assert f1_id in items_a
        assert items_a[f1_id]["my_role"] == "OWNER"
        assert f2_id in items_a
        assert items_a[f2_id]["my_role"] == "CAREGIVER"
        assert f3_id not in items_a
    finally:
        _cleanup([user_a_id, user_b_id], family_ids)


def test_list_families_archived_filtering():
    """TASK 04 §20: GET /families hides ARCHIVED by default, shows with include_archived=true."""
    user_id, _, token = _create_user_and_token("list_arch")
    family_ids: list[int] = []

    try:
        f_res = client.post(
            "/families",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Gia đình Lưu Trữ"},
        )
        f_id = f_res.json()["id"]
        family_ids.append(f_id)

        arch_res = client.post(
            f"/families/{f_id}/archive",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert arch_res.status_code == 200
        assert arch_res.json()["status"] == "ARCHIVED"

        default_list = client.get(
            "/families",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert default_list.status_code == 200
        default_ids = [item["id"] for item in default_list.json()["items"]]
        assert f_id not in default_ids

        with_archived = client.get(
            "/families?include_archived=true",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert with_archived.status_code == 200
        archived_items = {
            item["id"]: item for item in with_archived.json()["items"]
        }
        assert f_id in archived_items
        assert archived_items[f_id]["status"] == "ARCHIVED"
    finally:
        _cleanup([user_id], family_ids)

