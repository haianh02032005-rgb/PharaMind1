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


def test_member_role_matrix_viewer_caregiver_admin_owner():
    """TASK 05 §49, §69, §72: Role matrix enforcement across member and health endpoints."""
    owner_id, _, owner_token = _create_user_and_token("auth_owner")
    admin_id, admin_email, admin_token = _create_user_and_token("auth_admin")
    cg_id, cg_email, cg_token = _create_user_and_token("auth_cg")
    vw_id, vw_email, vw_token = _create_user_and_token("auth_vw")
    family_ids: list[int] = []

    try:
        fam_id = client.post(
            "/families",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={"name": "Gia đình Phân Quyền"},
        ).json()["id"]
        family_ids.append(fam_id)

        for email, role in [
            (admin_email, "ADMIN"),
            (cg_email, "CAREGIVER"),
            (vw_email, "VIEWER"),
        ]:
            r = client.post(
                f"/families/{fam_id}/memberships",
                headers={"Authorization": f"Bearer {owner_token}"},
                json={"email": email, "role": role},
            )
            assert r.status_code == 201

        # VIEWER cannot create member (403)
        vw_create = client.post(
            f"/families/{fam_id}/members",
            headers={"Authorization": f"Bearer {vw_token}"},
            json={"full_name": "Viewer Member"},
        )
        assert vw_create.status_code == 403

        # CAREGIVER can create member (201)
        cg_create = client.post(
            f"/families/{fam_id}/members",
            headers={"Authorization": f"Bearer {cg_token}"},
            json={"full_name": "Bà Nội", "relationship_label": "Grandmother"},
        )
        assert cg_create.status_code == 201
        member_id = cg_create.json()["id"]

        # VIEWER can view member and health profile (200)
        vw_get = client.get(
            f"/families/{fam_id}/members/{member_id}",
            headers={"Authorization": f"Bearer {vw_token}"},
        )
        assert vw_get.status_code == 200

        vw_hp_get = client.get(
            f"/families/{fam_id}/members/{member_id}/health-profile",
            headers={"Authorization": f"Bearer {vw_token}"},
        )
        assert vw_hp_get.status_code == 200

        # VIEWER cannot update member or health profile (403)
        vw_upd = client.patch(
            f"/families/{fam_id}/members/{member_id}",
            headers={"Authorization": f"Bearer {vw_token}"},
            json={"full_name": "Viewer Hack"},
        )
        assert vw_upd.status_code == 403

        vw_hp_upd = client.patch(
            f"/families/{fam_id}/members/{member_id}/health-profile",
            headers={"Authorization": f"Bearer {vw_token}"},
            json={"height_cm": 160},
        )
        assert vw_hp_upd.status_code == 403

        # CAREGIVER can update member and health profile (200)
        cg_upd = client.patch(
            f"/families/{fam_id}/members/{member_id}",
            headers={"Authorization": f"Bearer {cg_token}"},
            json={"full_name": "Bà Nội Đã Cập Nhật"},
        )
        assert cg_upd.status_code == 200
        assert cg_upd.json()["full_name"] == "Bà Nội Đã Cập Nhật"

        cg_hp_upd = client.patch(
            f"/families/{fam_id}/members/{member_id}/health-profile",
            headers={"Authorization": f"Bearer {cg_token}"},
            json={"height_cm": 155, "weight_kg": 52},
        )
        assert cg_hp_upd.status_code == 200

        # CAREGIVER cannot archive member (403)
        cg_arch = client.post(
            f"/families/{fam_id}/members/{member_id}/archive",
            headers={"Authorization": f"Bearer {cg_token}"},
        )
        assert cg_arch.status_code == 403

        # ADMIN can archive and restore member (200)
        adm_arch = client.post(
            f"/families/{fam_id}/members/{member_id}/archive",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert adm_arch.status_code == 200
        assert adm_arch.json()["status"] == "ARCHIVED"

        adm_rest = client.post(
            f"/families/{fam_id}/members/{member_id}/restore",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert adm_rest.status_code == 200
        assert adm_rest.json()["status"] == "ACTIVE"
    finally:
        _cleanup([owner_id, admin_id, cg_id, vw_id], family_ids)


def test_cross_family_member_access_returns_404():
    """TASK 05 §47, §48, §71: Accessing a member across families returns 404 Not Found."""
    owner_a_id, _, token_a = _create_user_and_token("x_fam_a")
    owner_b_id, _, token_b = _create_user_and_token("x_fam_b")
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

        member_a_id = client.post(
            f"/families/{fam_a}/members",
            headers={"Authorization": f"Bearer {token_a}"},
            json={"full_name": "Member of Family A"},
        ).json()["id"]

        # User B trying /families/{fam_a}/members/{member_a_id} -> 404
        res_direct = client.get(
            f"/families/{fam_a}/members/{member_a_id}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert res_direct.status_code == 404

        # User B trying /families/{fam_b}/members/{member_a_id} (IDOR via own family) -> 404
        res_idor = client.get(
            f"/families/{fam_b}/members/{member_a_id}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert res_idor.status_code == 404

        res_hp_idor = client.get(
            f"/families/{fam_b}/members/{member_a_id}/health-profile",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert res_hp_idor.status_code == 404
    finally:
        _cleanup([owner_a_id, owner_b_id], family_ids)


def test_archived_member_and_archived_family_reject_writes():
    """TASK 05 §50, §51, §78: Archived member or archived family rejects health/member writes with 409."""
    owner_id, _, token = _create_user_and_token("arch_rule_owner")
    family_ids: list[int] = []

    try:
        fam_id = client.post(
            "/families",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Family Archive Rule"},
        ).json()["id"]
        family_ids.append(fam_id)

        mem_id = client.post(
            f"/families/{fam_id}/members",
            headers={"Authorization": f"Bearer {token}"},
            json={"full_name": "Member To Archive"},
        ).json()["id"]

        # Archive member
        client.post(
            f"/families/{fam_id}/members/{mem_id}/archive",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Viewing archived member and health profile still works
        assert (
            client.get(
                f"/families/{fam_id}/members/{mem_id}",
                headers={"Authorization": f"Bearer {token}"},
            ).status_code
            == 200
        )
        assert (
            client.get(
                f"/families/{fam_id}/members/{mem_id}/health-profile",
                headers={"Authorization": f"Bearer {token}"},
            ).status_code
            == 200
        )

        # Updating archived member or adding health records fails with 409
        assert (
            client.patch(
                f"/families/{fam_id}/members/{mem_id}/health-profile",
                headers={"Authorization": f"Bearer {token}"},
                json={"height_cm": 165},
            ).status_code
            == 409
        )
        assert (
            client.post(
                f"/families/{fam_id}/members/{mem_id}/conditions",
                headers={"Authorization": f"Bearer {token}"},
                json={"name": "Tăng huyết áp"},
            ).status_code
            == 409
        )
        assert (
            client.post(
                f"/families/{fam_id}/members/{mem_id}/allergies",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "allergen": "Penicillin",
                    "allergy_type": "DRUG",
                    "severity": "SEVERE",
                },
            ).status_code
            == 409
        )
        assert (
            client.post(
                f"/families/{fam_id}/members/{mem_id}/drug-reactions",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "drug_name": "Aspirin",
                    "reaction": "Đau dạ dày",
                    "severity": "MILD",
                },
            ).status_code
            == 409
        )

        # Restore member, then archive Family
        client.post(
            f"/families/{fam_id}/members/{mem_id}/restore",
            headers={"Authorization": f"Bearer {token}"},
        )
        client.post(
            f"/families/{fam_id}/archive",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Creating member in archived family fails with 409
        assert (
            client.post(
                f"/families/{fam_id}/members",
                headers={"Authorization": f"Bearer {token}"},
                json={"full_name": "New Member While Family Archived"},
            ).status_code
            == 409
        )
    finally:
        _cleanup([owner_id], family_ids)

