from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import delete

from backend.app.core.security import verify_password
from backend.app.db.session import SessionLocal
from backend.app.main import app
from backend.app.models.user import User
from backend.app.modules.users.repository import UserRepository


client = TestClient(app)


def _unique_email(prefix: str = "reg") -> str:
    return f"{prefix}_{uuid4().hex[:10]}@example.com"


def _cleanup_user(email: str) -> None:
    with SessionLocal() as session:
        session.execute(delete(User).where(User.email == email.strip().lower()))
        session.commit()


def test_register_success():
    email = _unique_email("register_ok")
    try:
        response = client.post(
            "/auth/register",
            json={
                "email": email,
                "password": "StrongPass123",
                "full_name": "Nguyen Van A",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["id"] > 0
        assert data["email"] == email
        assert data["full_name"] == "Nguyen Van A"
        assert data["status"] == "ACTIVE"
        assert data["is_email_verified"] is False
        assert "password" not in data
        assert "password_hash" not in data

        with SessionLocal() as session:
            user = UserRepository().get_by_email(session, email)
            assert user is not None
            assert user.id == data["id"]
            assert user.email == email
    finally:
        _cleanup_user(email)


def test_register_duplicate_email():
    email = _unique_email("duplicate")
    payload = {
        "email": email,
        "password": "StrongPass123",
        "full_name": "Nguyen Van A",
    }
    try:
        first_response = client.post("/auth/register", json=payload)
        assert first_response.status_code == 201

        second_response = client.post("/auth/register", json=payload)
        assert second_response.status_code == 409
        assert second_response.json() == {
            "detail": "Email already registered",
        }
    finally:
        _cleanup_user(email)


def test_register_email_normalization():
    token = uuid4().hex[:10]
    raw_email = f"  TEST_{token}@EXAMPLE.COM  "
    normalized_email = f"test_{token}@example.com"
    try:
        response = client.post(
            "/auth/register",
            json={
                "email": raw_email,
                "password": "StrongPass123",
                "full_name": "Tran Thi B",
            },
        )
        assert response.status_code == 201
        assert response.json()["email"] == normalized_email

        login_response = client.post(
            "/auth/login",
            json={
                "email": normalized_email,
                "password": "StrongPass123",
            },
        )
        assert login_response.status_code == 200
    finally:
        _cleanup_user(normalized_email)


def test_register_password_hashing():
    email = _unique_email("pw_hash")
    plain_password = "MySecretPassword123"
    try:
        response = client.post(
            "/auth/register",
            json={
                "email": email,
                "password": plain_password,
                "full_name": "Le Van C",
            },
        )
        assert response.status_code == 201

        with SessionLocal() as session:
            user = UserRepository().get_by_email(session, email)
            assert user is not None
            assert user.password_hash != plain_password
            assert plain_password not in user.password_hash
            assert user.password_hash.startswith("$argon2")
            assert verify_password(plain_password, user.password_hash) is True
    finally:
        _cleanup_user(email)


def test_register_rejects_short_password():
    email = _unique_email("short_pw")
    response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "short",
            "full_name": "Short Password User",
        },
    )
    assert response.status_code == 422

