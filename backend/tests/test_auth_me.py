from datetime import timedelta
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import delete

from backend.app.core.security import create_access_token
from backend.app.db.session import SessionLocal
from backend.app.main import app
from backend.app.models.user import User, UserStatus
from backend.app.modules.users.repository import UserRepository


client = TestClient(app)


def _unique_email(prefix: str = "me") -> str:
    return f"{prefix}_{uuid4().hex[:10]}@example.com"


def _cleanup_user(email: str) -> None:
    with SessionLocal() as session:
        session.execute(delete(User).where(User.email == email.strip().lower()))
        session.commit()


def test_get_me_success():
    email = _unique_email("me_ok")
    password = "StrongPass123"
    try:
        reg_res = client.post(
            "/auth/register",
            json={
                "email": email,
                "password": password,
                "full_name": "Nguyen Thi Lan",
            },
        )
        assert reg_res.status_code == 201
        user_id = reg_res.json()["id"]

        login_res = client.post(
            "/auth/login",
            json={"email": email, "password": password},
        )
        access_token = login_res.json()["access_token"]

        me_res = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert me_res.status_code == 200
        body = me_res.json()
        assert body["id"] == user_id
        assert body["email"] == email
        assert body["full_name"] == "Nguyen Thi Lan"
        assert body["status"] == "ACTIVE"
        assert body["is_email_verified"] is False
        assert "password_hash" not in body
        assert "password" not in body
    finally:
        _cleanup_user(email)


def test_get_me_without_token():
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_get_me_invalid_token():
    response = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer abc.invalid.token"},
    )
    assert response.status_code == 401


def test_get_me_expired_token():
    email = _unique_email("expired")
    try:
        reg_res = client.post(
            "/auth/register",
            json={
                "email": email,
                "password": "StrongPass123",
                "full_name": "Expired Token User",
            },
        )
        user_id = reg_res.json()["id"]

        expired_token = create_access_token(
            user_id,
            expires_delta=timedelta(seconds=-10),
        )

        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert response.status_code == 401
    finally:
        _cleanup_user(email)


def test_get_me_blocked_user():
    email = _unique_email("me_blocked")
    password = "StrongPass123"
    try:
        client.post(
            "/auth/register",
            json={
                "email": email,
                "password": password,
                "full_name": "Blocked Me User",
            },
        )
        login_res = client.post(
            "/auth/login",
            json={"email": email, "password": password},
        )
        access_token = login_res.json()["access_token"]

        with SessionLocal() as session:
            user = UserRepository().get_by_email(session, email)
            assert user is not None
            user.status = UserStatus.BLOCKED.value
            session.commit()

        me_res = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert me_res.status_code == 403
    finally:
        _cleanup_user(email)

