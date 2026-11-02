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


def test_cabinet_authorization_matrix_cross_family_and_archive():
    """TASK 09 §39, §61–64, §68: Role matrix (OWNER/ADMIN create & archive, CAREGIVER operates compartments/simulator, VIEWER read-only), cross-family 404, archived cabinet blocks commands."""
    owner_id, _, owner_token = _create_user_and_token("cab_auth_owner")
    caregiver_id, cg_email, cg_token = _create_user_and_token("cab_auth_cg")
    viewer_id, viewer_email, viewer_token = _create_user_and_token(
        "cab_auth_viewer"
    )
    outsider_id, _, outsider_token = _create_user_and_token(
        "cab_auth_outsider"
    )
    family_ids: list[int] = []

    try:
        fam_a = client.post(
            "/families",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={"name": "Family A"},
        ).json()["id"]
        family_ids.append(fam_a)

        fam_b = client.post(
            "/families",
            headers={"Authorization": f"Bearer {outsider_token}"},
            json={"name": "Family B"},
        ).json()["id"]
        family_ids.append(fam_b)

        client.post(
            f"/families/{fam_a}/memberships",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={"email": cg_email, "role": "CAREGIVER"},
        )
        client.post(
            f"/families/{fam_a}/memberships",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={"email": viewer_email, "role": "VIEWER"},
        )

        # 1. CAREGIVER & VIEWER cannot create cabinet -> 403 (§61)
        assert (
            client.post(
                f"/families/{fam_a}/cabinets",
                headers={"Authorization": f"Bearer {cg_token}"},
                json={
                    "name": "CG Cab",
                    "device_code": f"PM-CAB-{uuid4().hex[:8].upper()}",
                },
            ).status_code
            == 403
        )
        assert (
            client.post(
                f"/families/{fam_a}/cabinets",
                headers={"Authorization": f"Bearer {viewer_token}"},
                json={
                    "name": "Viewer Cab",
                    "device_code": f"PM-CAB-{uuid4().hex[:8].upper()}",
                },
            ).status_code
            == 403
        )

        # 2. OWNER creates cabinet -> 201
        cab_id = client.post(
            f"/families/{fam_a}/cabinets",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={
                "name": "Tủ chính",
                "device_code": f"PM-CAB-{uuid4().hex[:8].upper()}",
            },
        ).json()["id"]

        # 3. CAREGIVER can bring simulator online and open compartment -> 200 (§61)
        assert (
            client.post(
                f"/families/{fam_a}/cabinets/{cab_id}/simulator/online",
                headers={"Authorization": f"Bearer {cg_token}"},
            ).status_code
            == 200
        )
        assert (
            client.post(
                f"/families/{fam_a}/cabinets/{cab_id}/compartments/1/open",
                headers={"Authorization": f"Bearer {cg_token}"},
            ).status_code
            == 200
        )

        # 4. VIEWER can view cabinet, state, compartments, events -> 200, but cannot open/close -> 403 (§61)
        assert (
            client.get(
                f"/families/{fam_a}/cabinets/{cab_id}",
                headers={"Authorization": f"Bearer {viewer_token}"},
            ).status_code
            == 200
        )
        assert (
            client.get(
                f"/families/{fam_a}/cabinets/{cab_id}/state",
                headers={"Authorization": f"Bearer {viewer_token}"},
            ).status_code
            == 200
        )
        assert (
            client.post(
                f"/families/{fam_a}/cabinets/{cab_id}/compartments/1/close",
                headers={"Authorization": f"Bearer {viewer_token}"},
            ).status_code
            == 403
        )

        # 5. Cross-family read from Family B -> 404 (§64)
        assert (
            client.get(
                f"/families/{fam_b}/cabinets/{cab_id}",
                headers={"Authorization": f"Bearer {outsider_token}"},
            ).status_code
            == 404
        )

        # 6. CAREGIVER cannot archive cabinet -> 403; OWNER archives -> 200 (§61, §68)
        assert (
            client.post(
                f"/families/{fam_a}/cabinets/{cab_id}/archive",
                headers={"Authorization": f"Bearer {cg_token}"},
            ).status_code
            == 403
        )
        arch_res = client.post(
            f"/families/{fam_a}/cabinets/{cab_id}/archive",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert arch_res.status_code == 200
        assert arch_res.json()["status"] == "ARCHIVED"

        # 7. Archived cabinet blocks simulator/compartment commands -> 409 (§39)
        assert (
            client.post(
                f"/families/{fam_a}/cabinets/{cab_id}/simulator/online",
                headers={"Authorization": f"Bearer {owner_token}"},
            ).status_code
            == 409
        )
        assert (
            client.post(
                f"/families/{fam_a}/cabinets/{cab_id}/compartments/1/close",
                headers={"Authorization": f"Bearer {owner_token}"},
            ).status_code
            == 409
        )
    finally:
        _cleanup([owner_id, caregiver_id, viewer_id, outsider_id], family_ids)

