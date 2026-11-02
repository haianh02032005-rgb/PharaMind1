from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import delete

from backend.app.db.session import SessionLocal
from backend.app.main import app
from backend.app.models.cabinet import Cabinet
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
            session.execute(
                delete(Cabinet).where(Cabinet.family_id.in_(family_ids))
            )
            session.execute(delete(Family).where(Family.id.in_(family_ids)))
        if user_ids:
            session.execute(delete(User).where(User.id.in_(user_ids)))
        session.commit()


def test_create_cabinet_auto_9_compartments_duplicate_device_code_and_second_active_cabinet():
    """TASK 09 §12, §23–28, §77–80: Create cabinet auto-creates 9 compartments (positions 1..9), rejects duplicate device_code (409) & second active cabinet (409)."""
    user_id, _, token = _create_user_and_token("cab_create")
    family_ids: list[int] = []

    try:
        fam_1 = client.post(
            "/families",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Cabinet Family 1"},
        ).json()["id"]
        family_ids.append(fam_1)

        fam_2 = client.post(
            "/families",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Cabinet Family 2"},
        ).json()["id"]
        family_ids.append(fam_2)

        dev_code = f"PM-CAB-{uuid4().hex[:8].upper()}"

        # 1. Create cabinet -> 201 with 9 compartments (§77, §80)
        res = client.post(
            f"/families/{fam_1}/cabinets",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "Tủ thuốc gia đình",
                "device_code": dev_code,
            },
        )
        assert res.status_code == 201
        cab = res.json()
        cab_id = cab["id"]
        assert cab["family_id"] == fam_1
        assert cab["name"] == "Tủ thuốc gia đình"
        assert cab["device_code"] == dev_code
        assert cab["status"] == "OFFLINE"
        assert cab["hardware_mode"] == "SIMULATOR"
        assert len(cab["compartments"]) == 9
        assert [c["position"] for c in cab["compartments"]] == list(
            range(1, 10)
        )
        assert [c["object_id"] for c in cab["compartments"]] == [
            f"drawer_{pos:02d}" for pos in range(1, 10)
        ]
        assert all(c["status"] == "EMPTY" for c in cab["compartments"])
        assert all(c["is_open"] is False for c in cab["compartments"])

        # 2. Second active cabinet in same family -> 409 (§79)
        second_res = client.post(
            f"/families/{fam_1}/cabinets",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "Tủ thứ 2",
                "device_code": f"PM-CAB-{uuid4().hex[:8].upper()}",
            },
        )
        assert second_res.status_code == 409

        # 3. Duplicate device_code in another family -> 409 (§78)
        dup_code_res = client.post(
            f"/families/{fam_2}/cabinets",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "Tủ trùng mã",
                "device_code": dev_code,
            },
        )
        assert dup_code_res.status_code == 409

        # 4. List cabinets & list compartments (§26–28)
        list_res = client.get(
            f"/families/{fam_1}/cabinets",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert list_res.status_code == 200
        assert [c["id"] for c in list_res.json()["items"]] == [cab_id]

        comps_res = client.get(
            f"/families/{fam_1}/cabinets/{cab_id}/compartments",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert comps_res.status_code == 200
        assert [c["position"] for c in comps_res.json()["items"]] == list(
            range(1, 10)
        )
    finally:
        _cleanup([user_id], family_ids)

