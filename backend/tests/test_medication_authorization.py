from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import delete

from backend.app.db.session import SessionLocal
from backend.app.main import app
from backend.app.models.family import Family
from backend.app.models.medication_catalog import MedicationCatalog
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


def _cleanup(
    user_ids: list[int],
    family_ids: list[int],
    catalog_ids: list[int],
) -> None:
    with SessionLocal() as session:
        if family_ids:
            session.execute(delete(Family).where(Family.id.in_(family_ids)))
        if catalog_ids:
            session.execute(
                delete(MedicationCatalog).where(
                    MedicationCatalog.id.in_(catalog_ids)
                )
            )
        if user_ids:
            session.execute(delete(User).where(User.id.in_(user_ids)))
        session.commit()


def test_medication_role_matrix_and_cross_family_protection():
    """TASK 06 §47, §51, §52, §72–74: Role matrix and cross-family isolation."""
    owner_id, _, owner_token = _create_user_and_token("med_auth_owner")
    admin_id, admin_email, admin_token = _create_user_and_token("med_auth_admin")
    cg_id, cg_email, cg_token = _create_user_and_token("med_auth_cg")
    vw_id, vw_email, vw_token = _create_user_and_token("med_auth_vw")
    outsider_id, _, outsider_token = _create_user_and_token("med_auth_out")
    family_ids: list[int] = []
    catalog_ids: list[int] = []

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

        # VIEWER cannot create medication (403)
        vw_create = client.post(
            f"/families/{fam_a}/medications",
            headers={"Authorization": f"Bearer {vw_token}"},
            json={"name": "ViewerMed", "quantity": 10, "unit": "TABLET"},
        )
        assert vw_create.status_code == 403

        # CAREGIVER can create medication (201)
        cg_create = client.post(
            f"/families/{fam_a}/medications",
            headers={"Authorization": f"Bearer {cg_token}"},
            json={
                "name": f"Omeprazole-{uuid4().hex[:6]}",
                "quantity": 20,
                "unit": "CAPSULE",
            },
        )
        assert cg_create.status_code == 201
        med_id = cg_create.json()["id"]
        catalog_ids.append(cg_create.json()["catalog"]["id"])

        # VIEWER can view medication (200) but cannot update inventory (403)
        assert (
            client.get(
                f"/families/{fam_a}/medications/{med_id}",
                headers={"Authorization": f"Bearer {vw_token}"},
            ).status_code
            == 200
        )
        assert (
            client.patch(
                f"/families/{fam_a}/medications/{med_id}/inventory",
                headers={"Authorization": f"Bearer {vw_token}"},
                json={"quantity": 10},
            ).status_code
            == 403
        )

        # CAREGIVER can update inventory (200)
        cg_inv = client.patch(
            f"/families/{fam_a}/medications/{med_id}/inventory",
            headers={"Authorization": f"Bearer {cg_token}"},
            json={"quantity": 18},
        )
        assert cg_inv.status_code == 200
        assert cg_inv.json()["quantity"] == 18

        # CAREGIVER cannot archive medication (403)
        cg_arch = client.post(
            f"/families/{fam_a}/medications/{med_id}/archive",
            headers={"Authorization": f"Bearer {cg_token}"},
        )
        assert cg_arch.status_code == 403

        # OWNER and ADMIN can archive and restore medication (200)
        owner_arch = client.post(
            f"/families/{fam_a}/medications/{med_id}/archive",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert owner_arch.status_code == 200
        assert owner_arch.json()["status"] == "ARCHIVED"

        admin_rest = client.post(
            f"/families/{fam_a}/medications/{med_id}/restore",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert admin_rest.status_code == 200
        assert admin_rest.json()["status"] == "ACTIVE"

        # Cross-family IDOR protection: outsider accessing via Family B URL gets 404
        idor_get = client.get(
            f"/families/{fam_b}/medications/{med_id}",
            headers={"Authorization": f"Bearer {outsider_token}"},
        )
        assert idor_get.status_code == 404
    finally:
        _cleanup(
            [owner_id, admin_id, cg_id, vw_id, outsider_id],
            family_ids,
            catalog_ids,
        )

