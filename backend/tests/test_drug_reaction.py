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


def test_drug_reaction_crud_does_not_create_allergy_profile():
    """TASK 05 §21, §22, §43, §66, §76: DrugReactionHistory is strictly separate from AllergyProfile."""
    owner_id, _, token = _create_user_and_token("dr_owner")
    family_ids: list[int] = []

    try:
        fam_id = client.post(
            "/families",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Gia đình Phản Ứng Thuốc"},
        ).json()["id"]
        family_ids.append(fam_id)

        mem_id = client.post(
            f"/families/{fam_id}/members",
            headers={"Authorization": f"Bearer {token}"},
            json={"full_name": "Bà Lan"},
        ).json()["id"]

        create_res = client.post(
            f"/families/{fam_id}/members/{mem_id}/drug-reactions",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "drug_name": "Amoxicillin",
                "active_ingredient": "Amoxicillin",
                "reaction": "Phát ban",
                "severity": "MODERATE",
                "occurred_at": "2021-05-01",
                "confirmed_by_professional": False,
                "notes": "Cần hỏi lại bác sĩ lần khám tới",
            },
        )
        assert create_res.status_code == 201
        dr = create_res.json()
        dr_id = dr["id"]
        assert dr["drug_name"] == "Amoxicillin"
        assert dr["confirmed_by_professional"] is False

        # Must NOT automatically create an AllergyProfile (TASK 05 §22, §76)
        allergies_res = client.get(
            f"/families/{fam_id}/members/{mem_id}/allergies",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert allergies_res.status_code == 200
        assert allergies_res.json()["items"] == []

        # List drug reactions
        list_res = client.get(
            f"/families/{fam_id}/members/{mem_id}/drug-reactions",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert list_res.status_code == 200
        assert len(list_res.json()["items"]) == 1

        # Update drug reaction
        upd_res = client.patch(
            f"/families/{fam_id}/members/{mem_id}/drug-reactions/{dr_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"confirmed_by_professional": True, "severity": "SEVERE"},
        )
        assert upd_res.status_code == 200
        assert upd_res.json()["confirmed_by_professional"] is True
        assert upd_res.json()["severity"] == "SEVERE"

        # Still no AllergyProfile created automatically
        allergies_after = client.get(
            f"/families/{fam_id}/members/{mem_id}/allergies",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert allergies_after.json()["items"] == []

        # Delete drug reaction
        del_res = client.delete(
            f"/families/{fam_id}/members/{mem_id}/drug-reactions/{dr_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert del_res.status_code == 204
    finally:
        _cleanup([owner_id], family_ids)

