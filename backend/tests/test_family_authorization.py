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


def test_family_isolation_returns_404_for_outsider():
    """TASK 04 §22, §51: User outside a family receives 404 Not Found."""
    owner_id, _, owner_token = _create_user_and_token("iso_owner")
    outsider_id, _, outsider_token = _create_user_and_token("iso_outsider")
    family_ids: list[int] = []

    try:
        fam_res = client.post(
            "/families",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={"name": "Gia đình Riêng Tư"},
        )
        fam_id = fam_res.json()["id"]
        family_ids.append(fam_id)

        get_res = client.get(
            f"/families/{fam_id}",
            headers={"Authorization": f"Bearer {outsider_token}"},
        )
        assert get_res.status_code == 404

        patch_res = client.patch(
            f"/families/{fam_id}",
            headers={"Authorization": f"Bearer {outsider_token}"},
            json={"name": "Hack Name"},
        )
        assert patch_res.status_code == 404

        members_res = client.get(
            f"/families/{fam_id}/memberships",
            headers={"Authorization": f"Bearer {outsider_token}"},
        )
        assert members_res.status_code == 404
    finally:
        _cleanup([owner_id, outsider_id], family_ids)


def test_update_family_role_matrix_and_status_field_forbidden():
    """TASK 04 §23, §38, §52: OWNER & ADMIN can update; CAREGIVER & VIEWER cannot."""
    owner_id, _, owner_token = _create_user_and_token("upd_owner")
    admin_id, admin_email, admin_token = _create_user_and_token("upd_admin")
    caregiver_id, caregiver_email, caregiver_token = _create_user_and_token("upd_cg")
    viewer_id, viewer_email, viewer_token = _create_user_and_token("upd_vw")
    family_ids: list[int] = []

    try:
        fam_res = client.post(
            "/families",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={"name": "Gia đình Ban Đầu", "description": "Mô tả 1"},
        )
        fam_id = fam_res.json()["id"]
        family_ids.append(fam_id)

        for email, role in [
            (admin_email, "ADMIN"),
            (caregiver_email, "CAREGIVER"),
            (viewer_email, "VIEWER"),
        ]:
            r = client.post(
                f"/families/{fam_id}/memberships",
                headers={"Authorization": f"Bearer {owner_token}"},
                json={"email": email, "role": role},
            )
            assert r.status_code == 201

        owner_patch = client.patch(
            f"/families/{fam_id}",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={"name": "Gia đình Owner Sửa"},
        )
        assert owner_patch.status_code == 200
        assert owner_patch.json()["name"] == "Gia đình Owner Sửa"

        admin_patch = client.patch(
            f"/families/{fam_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"description": "Gia đình tại Hà Nội"},
        )
        assert admin_patch.status_code == 200
        assert admin_patch.json()["description"] == "Gia đình tại Hà Nội"

        cg_patch = client.patch(
            f"/families/{fam_id}",
            headers={"Authorization": f"Bearer {caregiver_token}"},
            json={"name": "Caregiver Sửa"},
        )
        assert cg_patch.status_code == 403

        vw_patch = client.patch(
            f"/families/{fam_id}",
            headers={"Authorization": f"Bearer {viewer_token}"},
            json={"name": "Viewer Sửa"},
        )
        assert vw_patch.status_code == 403

        status_patch = client.patch(
            f"/families/{fam_id}",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={"name": "Valid", "status": "ARCHIVED"},
        )
        assert status_patch.status_code == 422
    finally:
        _cleanup(
            [owner_id, admin_id, caregiver_id, viewer_id],
            family_ids,
        )


def test_archive_and_restore_permissions_and_archived_rules():
    """TASK 04 §24, §25, §53, §61: Only OWNER can archive/restore; write blocked when archived."""
    owner_id, _, owner_token = _create_user_and_token("arch_owner")
    admin_id, admin_email, admin_token = _create_user_and_token("arch_admin")
    family_ids: list[int] = []

    try:
        fam_res = client.post(
            "/families",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={"name": "Gia đình Archive Test"},
        )
        fam_id = fam_res.json()["id"]
        family_ids.append(fam_id)

        client.post(
            f"/families/{fam_id}/memberships",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={"email": admin_email, "role": "ADMIN"},
        )

        admin_archive = client.post(
            f"/families/{fam_id}/archive",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert admin_archive.status_code == 403

        owner_archive = client.post(
            f"/families/{fam_id}/archive",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert owner_archive.status_code == 200
        assert owner_archive.json()["status"] == "ARCHIVED"

        owner_view = client.get(
            f"/families/{fam_id}",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert owner_view.status_code == 200
        assert owner_view.json()["status"] == "ARCHIVED"

        admin_view_archived = client.get(
            f"/families/{fam_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert admin_view_archived.status_code == 404

        update_while_archived = client.patch(
            f"/families/{fam_id}",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={"name": "Sửa khi đang archived"},
        )
        assert update_while_archived.status_code == 409

        restore_res = client.post(
            f"/families/{fam_id}/restore",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert restore_res.status_code == 200
        assert restore_res.json()["status"] == "ACTIVE"

        admin_view_restored = client.get(
            f"/families/{fam_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert admin_view_restored.status_code == 200
    finally:
        _cleanup([owner_id, admin_id], family_ids)

