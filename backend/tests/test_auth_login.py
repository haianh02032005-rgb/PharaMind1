from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import delete

from backend.app.core.security import decode_token
from backend.app.db.session import SessionLocal
from backend.app.main import app
from backend.app.models.user import User, UserStatus
from backend.app.modules.users.repository import UserRepository


client = TestClient(app)


def _unique_email(prefix: str = "login") -> str:
    return f"{prefix}_{uuid4().hex[:10]}@example.com"


def _cleanup_user(email: str) -> None:
    with SessionLocal() as session:
        session.execute(delete(User).where(User.email == email.strip().lower()))
        session.commit()


def test_login_success():
    email = _unique_email("login_ok")
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

        response = client.post(
            "/auth/login",
            json={
                "email": email,
                "password": password,
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["token_type"] == "bearer"
        assert isinstance(body["access_token"], str) and len(body["access_token"]) > 10
        assert isinstance(body["refresh_token"], str) and len(body["refresh_token"]) > 10

        access_claims = decode_token(body["access_token"])
        assert access_claims["sub"] == str(user_id)
        assert access_claims["type"] == "access"
        assert "iat" in access_claims
        assert "exp" in access_claims

        refresh_claims = decode_token(body["refresh_token"])
        assert refresh_claims["sub"] == str(user_id)
        assert refresh_claims["type"] == "refresh"
        assert "iat" in refresh_claims
        assert "exp" in refresh_claims
    finally:
        _cleanup_user(email)


def test_login_wrong_password():
    email = _unique_email("wrong_pw")
    try:
        client.post(
            "/auth/register",
            json={
                "email": email,
                "password": "CorrectPassword123",
                "full_name": "User Wrong Pass",
            },
        )

        response = client.post(
            "/auth/login",
            json={
                "email": email,
                "password": "WrongPassword999",
            },
        )
        assert response.status_code == 401
        assert response.json() == {
            "detail": "Invalid email or password",
        }
    finally:
        _cleanup_user(email)


def test_login_unknown_email():
    unknown_email = _unique_email("unknown")
    response = client.post(
        "/auth/login",
        json={
            "email": unknown_email,
            "password": "SomePassword123",
        },
    )
    assert response.status_code == 401
    assert response.json() == {
        "detail": "Invalid email or password",
    }


def test_login_blocked_user():
    email = _unique_email("blocked")
    password = "StrongPass123"
    try:
        client.post(
            "/auth/register",
            json={
                "email": email,
                "password": password,
                "full_name": "Blocked User",
            },
        )

        with SessionLocal() as session:
            user = UserRepository().get_by_email(session, email)
            assert user is not None
            user.status = UserStatus.BLOCKED.value
            session.commit()

        response = client.post(
            "/auth/login",
            json={
                "email": email,
                "password": password,
            },
        )
        assert response.status_code == 403
    finally:
        _cleanup_user(email)

