from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import delete

from backend.app.db.session import SessionLocal
from backend.app.main import app
from backend.app.models.family import Family
from backend.app.models.prescription import Prescription
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
            session.execute(
                delete(Prescription).where(
                    Prescription.family_id.in_(family_ids)
                )
            )
            session.execute(delete(Family).where(Family.id.in_(family_ids)))
        if user_ids:
            session.execute(delete(User).where(User.id.in_(user_ids)))
        session.commit()


def test_create_list_and_cross_family_member_prescription():
    """TASK 07 §14–16, §26–28, §51, §52: Create & list prescriptions, reject cross-family member (404)."""
    user_a_id, _, token_a = _create_user_and_token("rx_create_a")
    user_b_id, _, token_b = _create_user_and_token("rx_create_b")
    family_ids: list[int] = []

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

        member_a = client.post(
            f"/families/{fam_a}/members",
            headers={"Authorization": f"Bearer {token_a}"},
            json={"full_name": "Bà Nguyễn Thị Lan", "relationship_label": "Bà"},
        ).json()["id"]

        member_b = client.post(
            f"/families/{fam_b}/members",
            headers={"Authorization": f"Bearer {token_b}"},
            json={"full_name": "Thành viên B"},
        ).json()["id"]

        # Create prescription for member_a in fam_a -> 201
        res = client.post(
            f"/families/{fam_a}/prescriptions",
            headers={"Authorization": f"Bearer {token_a}"},
            json={
                "member_id": member_a,
                "title": "Đơn thuốc huyết áp",
                "doctor_name": "BS. Nguyễn Văn B",
                "facility_name": "Bệnh viện A",
                "issued_at": "2026-10-20",
                "start_date": "2026-10-20",
                "end_date": "2026-11-20",
                "notes": "Theo dõi huyết áp tại nhà",
            },
        )
        assert res.status_code == 201
        rx = res.json()
        rx_id = rx["id"]
        assert rx["family_id"] == fam_a
        assert rx["member_id"] == member_a
        assert rx["member"]["full_name"] == "Bà Nguyễn Thị Lan"
        assert rx["title"] == "Đơn thuốc huyết áp"
        assert rx["status"] == "ACTIVE"
        assert rx["items"] == []

        # Cross-family member: creating prescription in Family A with member_b -> 404
        cross_res = client.post(
            f"/families/{fam_a}/prescriptions",
            headers={"Authorization": f"Bearer {token_a}"},
            json={
                "member_id": member_b,
                "title": "Cross family member rx",
            },
        )
        assert cross_res.status_code == 404

        # List prescriptions in Family A & by Member
        list_res = client.get(
            f"/families/{fam_a}/prescriptions?member_id={member_a}",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert list_res.status_code == 200
        assert [p["id"] for p in list_res.json()["items"]] == [rx_id]

        mem_rx_res = client.get(
            f"/families/{fam_a}/members/{member_a}/prescriptions",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert mem_rx_res.status_code == 200
        assert [p["id"] for p in mem_rx_res.json()["items"]] == [rx_id]
    finally:
        _cleanup([user_a_id, user_b_id], family_ids)
