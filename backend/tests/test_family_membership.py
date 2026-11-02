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


def test_add_list_duplicate_and_unknown_membership():
    """TASK 04 §27-31, §54-56: Add existing user, reject unknown/duplicate/OWNER."""
    owner_id, _, owner_token = _create_user_and_token("mem_owner")
    cg_id, cg_email, cg_token = _create_user_and_token("mem_cg")
    family_ids: list[int] = []

    try:
        fam_res = client.post(
            "/families",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={"name": "Gia đình Membership"},
        )
        fam_id = fam_res.json()["id"]
        family_ids.append(fam_id)

        add_res = client.post(
            f"/families/{fam_id}/memberships",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={"email": f"  {cg_email.upper()}  ", "role": "CAREGIVER"},
        )
        assert add_res.status_code == 201
        add_body = add_res.json()
        assert add_body["role"] == "CAREGIVER"
        assert add_body["user"]["id"] == cg_id
        assert add_body["user"]["email"] == cg_email
        assert "password_hash" not in add_body["user"]

        dup_res = client.post(
            f"/families/{fam_id}/memberships",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={"email": cg_email, "role": "VIEWER"},
        )
        assert dup_res.status_code == 409
        assert dup_res.json() == {
            "detail": "User already belongs to this family",
        }

        unknown_res = client.post(
            f"/families/{fam_id}/memberships",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={
                "email": f"nonexistent_{uuid4().hex[:8]}@example.com",
                "role": "VIEWER",
            },
        )
        assert unknown_res.status_code == 404
        assert unknown_res.json() == {
            "detail": "User account not found",
        }

        owner_role_res = client.post(
            f"/families/{fam_id}/memberships",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={"email": cg_email, "role": "OWNER"},
        )
        assert owner_role_res.status_code == 403

        list_res = client.get(
            f"/families/{fam_id}/memberships",
            headers={"Authorization": f"Bearer {cg_token}"},
        )
        assert list_res.status_code == 200
        items = list_res.json()["items"]
        assert len(items) == 2
        for item in items:
            assert "password_hash" not in item["user"]
    finally:
        _cleanup([owner_id, cg_id], family_ids)


def test_owner_protection_role_update_and_removal_rules():
    """TASK 04 §32-34, §57: OWNER cannot be downgraded/deleted; ADMIN cannot remove ADMIN."""
    owner_id, _, owner_token = _create_user_and_token("prot_owner")
    admin1_id, admin1_email, admin1_token = _create_user_and_token("prot_admin1")
    admin2_id, admin2_email, _ = _create_user_and_token("prot_admin2")
    cg_id, cg_email, _ = _create_user_and_token("prot_cg")
    family_ids: list[int] = []

    try:
        fam_res = client.post(
            "/families",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={"name": "Gia đình Bảo Vệ Owner"},
        )
        fam_id = fam_res.json()["id"]
        family_ids.append(fam_id)

        members_list = client.get(
            f"/families/{fam_id}/memberships",
            headers={"Authorization": f"Bearer {owner_token}"},
        ).json()["items"]
        owner_membership_id = members_list[0]["id"]

        m_admin1 = client.post(
            f"/families/{fam_id}/memberships",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={"email": admin1_email, "role": "ADMIN"},
        ).json()
        m_admin2 = client.post(
            f"/families/{fam_id}/memberships",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={"email": admin2_email, "role": "ADMIN"},
        ).json()
        m_cg = client.post(
            f"/families/{fam_id}/memberships",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={"email": cg_email, "role": "CAREGIVER"},
        ).json()

        downgrade_owner = client.patch(
            f"/families/{fam_id}/memberships/{owner_membership_id}",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={"role": "VIEWER"},
        )
        assert downgrade_owner.status_code == 403

        delete_owner = client.delete(
            f"/families/{fam_id}/memberships/{owner_membership_id}",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert delete_owner.status_code == 403

        admin_change_role = client.patch(
            f"/families/{fam_id}/memberships/{m_cg['id']}",
            headers={"Authorization": f"Bearer {admin1_token}"},
            json={"role": "VIEWER"},
        )
        assert admin_change_role.status_code == 403

        owner_change_role = client.patch(
            f"/families/{fam_id}/memberships/{m_cg['id']}",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={"role": "VIEWER"},
        )
        assert owner_change_role.status_code == 200
        assert owner_change_role.json()["role"] == "VIEWER"

        promote_to_owner = client.patch(
            f"/families/{fam_id}/memberships/{m_cg['id']}",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={"role": "OWNER"},
        )
        assert promote_to_owner.status_code == 403

        admin_delete_other_admin = client.delete(
            f"/families/{fam_id}/memberships/{m_admin2['id']}",
            headers={"Authorization": f"Bearer {admin1_token}"},
        )
        assert admin_delete_other_admin.status_code == 403

        admin_delete_viewer = client.delete(
            f"/families/{fam_id}/memberships/{m_cg['id']}",
            headers={"Authorization": f"Bearer {admin1_token}"},
        )
        assert admin_delete_viewer.status_code == 204

        owner_delete_admin = client.delete(
            f"/families/{fam_id}/memberships/{m_admin1['id']}",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert owner_delete_admin.status_code == 204
    finally:
        _cleanup(
            [owner_id, admin1_id, admin2_id, cg_id],
            family_ids,
        )


def test_cross_family_membership_idor_attack_blocked():
    """TASK 04 §58, §59: Deleting/updating Family A membership via Family B URL must return 404."""
    owner_a_id, _, token_a = _create_user_and_token("idor_a")
    member_a_id, member_a_email, _ = _create_user_and_token("idor_mem_a")
    owner_b_id, _, token_b = _create_user_and_token("idor_b")
    family_ids: list[int] = []

    try:
        fam_a = client.post(
            "/families",
            headers={"Authorization": f"Bearer {token_a}"},
            json={"name": "Gia đình A"},
        ).json()
        fam_b = client.post(
            "/families",
            headers={"Authorization": f"Bearer {token_b}"},
            json={"name": "Gia đình B"},
        ).json()
        family_ids.extend([fam_a["id"], fam_b["id"]])

        mem_a = client.post(
            f"/families/{fam_a['id']}/memberships",
            headers={"Authorization": f"Bearer {token_a}"},
            json={"email": member_a_email, "role": "CAREGIVER"},
        ).json()

        cross_patch = client.patch(
            f"/families/{fam_b['id']}/memberships/{mem_a['id']}",
            headers={"Authorization": f"Bearer {token_b}"},
            json={"role": "VIEWER"},
        )
        assert cross_patch.status_code == 404

        cross_delete = client.delete(
            f"/families/{fam_b['id']}/memberships/{mem_a['id']}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert cross_delete.status_code == 404

        members_a = client.get(
            f"/families/{fam_a['id']}/memberships",
            headers={"Authorization": f"Bearer {token_a}"},
        ).json()["items"]
        assert any(m["id"] == mem_a["id"] and m["role"] == "CAREGIVER" for m in members_a)
    finally:
        _cleanup([owner_a_id, member_a_id, owner_b_id], family_ids)

