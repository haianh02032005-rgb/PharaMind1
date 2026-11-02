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


def test_link_unlink_duplicate_cross_family_and_archived_rules():
    """TASK 06 §19, §20, §42–46, §49, §50, §69–71, §75: Link/unlink medication and member with safety guards."""
    user_a_id, _, token_a = _create_user_and_token("med_link_a")
    user_b_id, _, token_b = _create_user_and_token("med_link_b")
    family_ids: list[int] = []
    catalog_ids: list[int] = []

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

        member_a1 = client.post(
            f"/families/{fam_a}/members",
            headers={"Authorization": f"Bearer {token_a}"},
            json={"full_name": "Bà Nguyễn Thị Lan", "relationship_label": "Bà"},
        ).json()["id"]

        member_a2 = client.post(
            f"/families/{fam_a}/members",
            headers={"Authorization": f"Bearer {token_a}"},
            json={"full_name": "Ông Nguyễn Văn Minh", "relationship_label": "Ông"},
        ).json()["id"]

        member_b1 = client.post(
            f"/families/{fam_b}/members",
            headers={"Authorization": f"Bearer {token_b}"},
            json={"full_name": "Thành viên Family B"},
        ).json()["id"]

        med_a = client.post(
            f"/families/{fam_a}/medications",
            headers={"Authorization": f"Bearer {token_a}"},
            json={
                "name": f"Atorvastatin-{uuid4().hex[:6]}",
                "quantity": 30,
                "unit": "TABLET",
            },
        ).json()
        med_a_id = med_a["id"]
        catalog_ids.append(med_a["catalog"]["id"])

        # 1. Link member_a1 to med_a -> 201
        link_res = client.post(
            f"/families/{fam_a}/medications/{med_a_id}/members",
            headers={"Authorization": f"Bearer {token_a}"},
            json={"member_id": member_a1},
        )
        assert link_res.status_code == 201
        assert link_res.json()["id"] == member_a1

        # 2. Duplicate link -> 409 Conflict
        dup_res = client.post(
            f"/families/{fam_a}/medications/{med_a_id}/members",
            headers={"Authorization": f"Bearer {token_a}"},
            json={"member_id": member_a1},
        )
        assert dup_res.status_code == 409

        # 3. Cross-family link (member_b1 into fam_a medication) -> 404 Not Found
        cross_res = client.post(
            f"/families/{fam_a}/medications/{med_a_id}/members",
            headers={"Authorization": f"Bearer {token_a}"},
            json={"member_id": member_b1},
        )
        assert cross_res.status_code == 404

        # 4. List medication members & get medication detail includes member_a1
        med_members = client.get(
            f"/families/{fam_a}/medications/{med_a_id}/members",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert med_members.status_code == 200
        assert [m["id"] for m in med_members.json()["items"]] == [member_a1]

        detail_res = client.get(
            f"/families/{fam_a}/medications/{med_a_id}",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert [m["id"] for m in detail_res.json()["members"]] == [member_a1]

        # 5. List member medications via /families/{fam_a}/members/{member_a1}/medications
        mem_meds = client.get(
            f"/families/{fam_a}/members/{member_a1}/medications",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert mem_meds.status_code == 200
        assert [m["id"] for m in mem_meds.json()["items"]] == [med_a_id]

        # 6. Archived Member cannot be linked -> 409
        client.post(
            f"/families/{fam_a}/members/{member_a2}/archive",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        arch_mem_link = client.post(
            f"/families/{fam_a}/medications/{med_a_id}/members",
            headers={"Authorization": f"Bearer {token_a}"},
            json={"member_id": member_a2},
        )
        assert arch_mem_link.status_code == 409

        # Restore member_a2, archive med_a -> Archived Medication cannot link -> 409
        client.post(
            f"/families/{fam_a}/members/{member_a2}/restore",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        client.post(
            f"/families/{fam_a}/medications/{med_a_id}/archive",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        arch_med_link = client.post(
            f"/families/{fam_a}/medications/{med_a_id}/members",
            headers={"Authorization": f"Bearer {token_a}"},
            json={"member_id": member_a2},
        )
        assert arch_med_link.status_code == 409

        # Restore med_a and unlink member_a1 -> 204
        client.post(
            f"/families/{fam_a}/medications/{med_a_id}/restore",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        unlink_res = client.delete(
            f"/families/{fam_a}/medications/{med_a_id}/members/{member_a1}",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert unlink_res.status_code == 204
    finally:
        _cleanup([user_a_id, user_b_id], family_ids, catalog_ids)

