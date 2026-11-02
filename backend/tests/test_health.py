from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
    }


def test_root():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "name": "PharmaMind AI",
        "status": "running",
        "version": "0.1.0",
    }
