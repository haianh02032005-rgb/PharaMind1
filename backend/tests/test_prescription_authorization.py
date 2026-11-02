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


def test_prescription_role_matrix_and_cross_family_isolation():
    """TASK 07 §37, §38, §40, §59, §62: Role matrix for OWNER/ADMIN/CAREGIVER/VIEWER and cross-family 404."""
    owner_id, _, owner_token = _create_user_and_token("rx_auth_owner")
    admin_id, admin_email, admin_token = _create_user_and_token("rx_auth_admin")
    cg_id, cg_email, cg_token = _create_user_and_token("rx_auth_cg")
    vw_id, vw_email, vw_token = _create_user_and_token("rx_auth_vw")
    outsider_id, _, outsider_token = _create_user_and_token("rx_auth_out")
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

        for email, role in [
            (admin_email, "ADMIN"),
            (cg_email, "CAREGIVER"),
            (vw_email, "VIEWER"),
        ]:
            r = client.post(
                f"/families/{fam_a}/memberships",
                headers={"Authorization": f"Bearer {owner_token}"},
                json={"email": email, "role": role},
            )
            assert r.status_code == 201

        member_id = client.post(
            f"/families/{fam_a}/members",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={"full_name": "Bà Lan"},
        ).json()["id"]

        # VIEWER cannot create prescription (403)
        assert (
            client.post(
                f"/families/{fam_a}/prescriptions",
                headers={"Authorization": f"Bearer {vw_token}"},
                json={"member_id": member_id, "title": "Viewer Rx"},
            ).status_code
            == 403
        )

        # CAREGIVER can create prescription (201)
        cg_rx = client.post(
            f"/families/{fam_a}/prescriptions",
            headers={"Authorization": f"Bearer {cg_token}"},
            json={"member_id": member_id, "title": "Caregiver Rx"},
        )
        assert cg_rx.status_code == 201
        rx_id = cg_rx.json()["id"]

        # VIEWER can view prescription (200)
        assert (
            client.get(
                f"/families/{fam_a}/prescriptions/{rx_id}",
                headers={"Authorization": f"Bearer {vw_token}"},
            ).status_code
            == 200
        )

        # CAREGIVER cannot archive prescription (403)
        assert (
            client.post(
                f"/families/{fam_a}/prescriptions/{rx_id}/archive",
                headers={"Authorization": f"Bearer {cg_token}"},
            ).status_code
            == 403
        )

        # OWNER and ADMIN can archive and restore prescription (200)
        assert (
            client.post(
                f"/families/{fam_a}/prescriptions/{rx_id}/archive",
                headers={"Authorization": f"Bearer {owner_token}"},
            ).status_code
            == 200
        )
        assert (
            client.post(
                f"/families/{fam_a}/prescriptions/{rx_id}/restore",
                headers={"Authorization": f"Bearer {admin_token}"},
            ).status_code
            == 200
        )

        # Cross-family read returns 404
        assert (
            client.get(
                f"/families/{fam_b}/prescriptions/{rx_id}",
                headers={"Authorization": f"Bearer {outsider_token}"},
            ).status_code
            == 404
        )
    finally:
        _cleanup(
            [owner_id, admin_id, cg_id, vw_id, outsider_id],
            family_ids,
        )
