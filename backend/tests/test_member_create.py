from datetime import date, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from backend.app.db.session import SessionLocal
from backend.app.main import app
from backend.app.models.family import Family
from backend.app.models.family_member import FamilyMember
from backend.app.models.health_profile import HealthProfile
from backend.app.models.user import User
from backend.app.modules.families.repository import FamilyRepository
from backend.app.modules.members.repository import MemberRepository
from backend.app.modules.members.schema import MemberCreateRequest
from backend.app.modules.members.service import MemberService


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


def test_create_member_creates_member_and_health_profile_in_db():
    """TASK 05 §15, §29, §68: Creating a Member automatically creates a 1-1 HealthProfile."""
    owner_id, _, token = _create_user_and_token("mem_create_owner")
    family_ids: list[int] = []

    try:
        fam_res = client.post(
            "/families",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Gia đình Nguyễn"},
        )
        assert fam_res.status_code == 201
        family_id = fam_res.json()["id"]
        family_ids.append(family_id)

        mem_res = client.post(
            f"/families/{family_id}/members",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "full_name": "  Bà Nguyễn Thị Lan  ",
                "date_of_birth": "1954-03-15",
                "gender": "FEMALE",
                "relationship_label": "Grandmother",
            },
        )
        assert mem_res.status_code == 201
        data = mem_res.json()
        assert data["family_id"] == family_id
        assert data["full_name"] == "Bà Nguyễn Thị Lan"
        assert data["date_of_birth"] == "1954-03-15"
        assert data["gender"] == "FEMALE"
        assert data["relationship_label"] == "Grandmother"
        assert data["status"] == "ACTIVE"
        member_id = data["id"]

        with SessionLocal() as session:
            db_member = session.scalar(
                select(FamilyMember).where(FamilyMember.id == member_id)
            )
            assert db_member is not None
            db_profile = session.scalar(
                select(HealthProfile).where(HealthProfile.member_id == member_id)
            )
            assert db_profile is not None
            assert db_profile.member_id == member_id
    finally:
        _cleanup([owner_id], family_ids)


def test_create_member_transaction_rolls_back_when_health_profile_fails():
    """TASK 05 §30: If HealthProfile creation fails, FamilyMember creation rolls back."""
    owner_id, _, token = _create_user_and_token("mem_tx_owner")
    family_ids: list[int] = []

    class FailingMemberRepository(MemberRepository):
        def create_health_profile(self, db, health_profile):
            raise RuntimeError("Simulated HealthProfile insert failure")

    try:
        fam_res = client.post(
            "/families",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Gia đình Rollback"},
        )
        family_id = fam_res.json()["id"]
        family_ids.append(family_id)

        with SessionLocal() as session:
            membership = FamilyRepository().get_membership(
                session, family_id=family_id, user_id=owner_id
            )
            assert membership is not None
            service = MemberService(repository=FailingMemberRepository())

            with pytest.raises(RuntimeError, match="Simulated HealthProfile"):
                service.create_member(
                    session,
                    membership,
                    MemberCreateRequest(
                        full_name="Orphan Member",
                        date_of_birth=date(1980, 1, 1),
                    ),
                )

        with SessionLocal() as check_session:
            members = list(
                check_session.scalars(
                    select(FamilyMember).where(
                        FamilyMember.family_id == family_id
                    )
                ).all()
            )
            assert members == []
    finally:
        _cleanup([owner_id], family_ids)


def test_create_member_rejects_future_date_of_birth_and_blank_name():
    """TASK 05 §56, §57, §74: Future date_of_birth and blank full_name return 422."""
    owner_id, _, token = _create_user_and_token("mem_val_owner")
    family_ids: list[int] = []

    try:
        fam_res = client.post(
            "/families",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Gia đình Validation"},
        )
        family_id = fam_res.json()["id"]
        family_ids.append(family_id)

        future_dob = (date.today() + timedelta(days=30)).isoformat()
        res_future = client.post(
            f"/families/{family_id}/members",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "full_name": "Người Tương Lai",
                "date_of_birth": future_dob,
            },
        )
        assert res_future.status_code == 422

        res_blank = client.post(
            f"/families/{family_id}/members",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "full_name": "   ",
                "date_of_birth": "1990-01-01",
            },
        )
        assert res_blank.status_code == 422
    finally:
        _cleanup([owner_id], family_ids)

