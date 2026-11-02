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


def test_health_profile_get_update_and_computed_bmi():
    """TASK 05 §11–15, §34–36, §72: Get & update health profile and verify computed BMI."""
    owner_id, _, token = _create_user_and_token("hp_owner")
    family_ids: list[int] = []

    try:
        fam_id = client.post(
            "/families",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Gia đình Sức Khỏe"},
        ).json()["id"]
        family_ids.append(fam_id)

        mem_id = client.post(
            f"/families/{fam_id}/members",
            headers={"Authorization": f"Bearer {token}"},
            json={"full_name": "Bà Nguyễn Thị Lan"},
        ).json()["id"]

        # Initial health profile has None blood_type and None bmi
        init_res = client.get(
            f"/families/{fam_id}/members/{mem_id}/health-profile",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert init_res.status_code == 200
        init_data = init_res.json()
        assert init_data["member_id"] == mem_id
        assert init_data["blood_type"] is None
        assert init_data["bmi"] is None

        # Update health profile
        upd_res = client.patch(
            f"/families/{fam_id}/members/{mem_id}/health-profile",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "blood_type": "O+",
                "height_cm": 160.0,
                "weight_kg": 64.0,
                "general_notes": "Theo dõi huyết áp thường xuyên",
            },
        )
        assert upd_res.status_code == 200
        upd_data = upd_res.json()
        assert upd_data["blood_type"] == "O+"
        assert upd_data["height_cm"] == 160.0
        assert upd_data["weight_kg"] == 64.0
        # BMI = 64 / (1.6 * 1.6) = 25.0
        assert upd_data["bmi"] == 25.0
        assert upd_data["general_notes"] == "Theo dõi huyết áp thường xuyên"
    finally:
        _cleanup([owner_id], family_ids)


def test_health_profile_rejects_invalid_height_and_weight():
    """TASK 05 §13, §14, §73: Invalid height_cm or weight_kg returns 422."""
    owner_id, _, token = _create_user_and_token("hp_val_owner")
    family_ids: list[int] = []

    try:
        fam_id = client.post(
            "/families",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Gia đình Validate HP"},
        ).json()["id"]
        family_ids.append(fam_id)

        mem_id = client.post(
            f"/families/{fam_id}/members",
            headers={"Authorization": f"Bearer {token}"},
            json={"full_name": "Ông Minh"},
        ).json()["id"]

        for bad_payload in [
            {"height_cm": -20},
            {"height_cm": 0},
            {"height_cm": 350},
            {"weight_kg": -5},
            {"weight_kg": 0},
            {"weight_kg": 600},
        ]:
            res = client.patch(
                f"/families/{fam_id}/members/{mem_id}/health-profile",
                headers={"Authorization": f"Bearer {token}"},
                json=bad_payload,
            )
            assert res.status_code == 422
    finally:
        _cleanup([owner_id], family_ids)
