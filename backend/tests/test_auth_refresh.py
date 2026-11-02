from datetime import timedelta
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import delete

from backend.app.core.security import create_refresh_token, decode_token
from backend.app.db.session import SessionLocal
from backend.app.main import app
from backend.app.models.user import User, UserStatus
from backend.app.modules.users.repository import UserRepository


client = TestClient(app)


def _unique_email(prefix: str = "refresh") -> str:
    return f"{prefix}_{uuid4().hex[:10]}@example.com"


def _cleanup_user(email: str) -> None:
    with SessionLocal() as session:
        session.execute(delete(User).where(User.email == email.strip().lower()))
        session.commit()


def test_refresh_token_success():
    email = _unique_email("refresh_ok")
    password = "StrongPass123"
    try:
        reg_res = client.post(
            "/auth/register",
            json={
                "email": email,
                "password": password,
                "full_name": "Refresh User",
            },
        )
        user_id = reg_res.json()["id"]

        login_res = client.post(
            "/auth/login",
            json={"email": email, "password": password},
        )
        refresh_token = login_res.json()["refresh_token"]

        refresh_res = client.post(
            "/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert refresh_res.status_code == 200
        data = refresh_res.json()
        assert data["token_type"] == "bearer"
        assert isinstance(data["access_token"], str) and len(data["access_token"]) > 10

        claims = decode_token(data["access_token"])
        assert claims["sub"] == str(user_id)
        assert claims["type"] == "access"

        me_res = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {data['access_token']}"},
        )
        assert me_res.status_code == 200
        assert me_res.json()["id"] == user_id
    finally:
        _cleanup_user(email)


def test_refresh_with_access_token_rejected():
    email = _unique_email("refresh_bad_type")
    password = "StrongPass123"
    try:
        client.post(
            "/auth/register",
            json={
                "email": email,
                "password": password,
                "full_name": "Wrong Token Type User",
            },
        )
        login_res = client.post(
            "/auth/login",
            json={"email": email, "password": password},
        )
        access_token = login_res.json()["access_token"]

        refresh_res = client.post(
            "/auth/refresh",
            json={"refresh_token": access_token},
        )
        assert refresh_res.status_code == 401
    finally:
        _cleanup_user(email)


def test_refresh_with_expired_token_rejected():
    email = _unique_email("refresh_expired")
    try:
        reg_res = client.post(
            "/auth/register",
            json={
                "email": email,
                "password": "StrongPass123",
                "full_name": "Expired Refresh User",
            },
        )
        user_id = reg_res.json()["id"]

        expired_refresh = create_refresh_token(
            user_id,
            expires_delta=timedelta(seconds=-10),
        )

        refresh_res = client.post(
            "/auth/refresh",
            json={"refresh_token": expired_refresh},
        )
        assert refresh_res.status_code == 401
    finally:
        _cleanup_user(email)


def test_refresh_blocked_user_rejected():
    email = _unique_email("refresh_blocked")
    password = "StrongPass123"
    try:
        client.post(
            "/auth/register",
            json={
                "email": email,
                "password": password,
                "full_name": "Blocked Refresh User",
            },
        )
        login_res = client.post(
            "/auth/login",
            json={"email": email, "password": password},
        )
        refresh_token = login_res.json()["refresh_token"]

        with SessionLocal() as session:
            user = UserRepository().get_by_email(session, email)
            assert user is not None
            user.status = UserStatus.BLOCKED.value
            session.commit()

        refresh_res = client.post(
            "/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert refresh_res.status_code == 403
    finally:
        _cleanup_user(email)

