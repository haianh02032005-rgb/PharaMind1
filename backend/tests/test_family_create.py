from uuid import uuid4

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import delete, select

from backend.app.db.session import SessionLocal
from backend.app.main import app
from backend.app.models.family import Family
from backend.app.models.family_membership import FamilyMembership
from backend.app.models.user import User
from backend.app.modules.families.repository import FamilyRepository
from backend.app.modules.families.schema import FamilyCreateRequest
from backend.app.modules.families.service import FamilyService
from backend.app.modules.users.service import UserService


client = TestClient(app)


def _register_and_login(prefix: str = "fam_create") -> tuple[int, str, str]:
    email = f"{prefix}_{uuid4().hex[:10]}@example.com"
    password = "StrongPass123"
    reg = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Family Creator",
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


def test_create_family_success():
    user_id, _, token = _register_and_login("create_ok")
    family_ids: list[int] = []
    try:
        response = client.post(
            "/families",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "  Gia đình Nguyễn Văn A  ",
                "description": "Gia đình chính",
            },
        )
        assert response.status_code == 201
        data = response.json()
        family_ids.append(data["id"])

        assert data["name"] == "Gia đình Nguyễn Văn A"
        assert data["description"] == "Gia đình chính"
        assert data["status"] == "ACTIVE"
        assert data["my_role"] == "OWNER"

        with SessionLocal() as session:
            family = session.get(Family, data["id"])
            assert family is not None
            assert family.name == "Gia đình Nguyễn Văn A"

            membership = FamilyRepository().get_membership(
                session,
                family_id=data["id"],
                user_id=user_id,
            )
            assert membership is not None
            assert membership.role == "OWNER"
    finally:
        _cleanup([user_id], family_ids)


def test_create_family_requires_auth():
    response = client.post(
        "/families",
        json={"name": "Unauthorized Family"},
    )
    assert response.status_code == 401


def test_create_family_rejects_blank_name():
    user_id, _, token = _register_and_login("blank_name")
    try:
        response = client.post(
            "/families",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "     "},
        )
        assert response.status_code == 422
    finally:
        _cleanup([user_id], [])


def test_create_family_transaction_rolls_back_on_membership_error():
    """TASK 04 §16, §49: If creating OWNER membership fails, Family must not be committed."""
    unique_family_name = f"Rollback_Family_{uuid4().hex[:10]}"
    email = f"tx_rollback_{uuid4().hex[:10]}@example.com"
    user_ids: list[int] = []

    class FailingMembershipRepository(FamilyRepository):
        def create_membership(self, db, membership):
            raise RuntimeError("Simulated failure creating OWNER membership")

    try:
        with SessionLocal() as session:
            user = UserService().create_user(
                session,
                email=email,
                password="StrongPass123",
                full_name="Tx User",
            )
            user_ids.append(user.id)

            service = FamilyService(repository=FailingMembershipRepository())
            with pytest.raises(RuntimeError, match="Simulated failure"):
                service.create_family(
                    session,
                    user,
                    FamilyCreateRequest(name=unique_family_name),
                )

        with SessionLocal() as check_session:
            stmt = select(Family).where(Family.name == unique_family_name)
            persisted = check_session.execute(stmt).scalar_one_or_none()
            assert persisted is None
    finally:
        _cleanup(user_ids, [])

