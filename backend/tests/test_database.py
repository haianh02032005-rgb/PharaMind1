from fastapi.testclient import TestClient
from sqlalchemy import inspect, text

from backend.app.db.session import SessionLocal, engine
from backend.app.main import app


client = TestClient(app)


def test_database_connection():
    with SessionLocal() as session:
        result = session.execute(
            text("SELECT 1")
        ).scalar_one()

    assert result == 1


def test_database_health_endpoint():
    response = client.get("/health/db")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "database": "connected",
    }


def test_migration_tables_exist():
    """`alembic upgrade head` must have created these tables."""
    tables = inspect(engine).get_table_names()

    assert "alembic_version" in tables
    assert "system_info" in tables
    assert "users" in tables
    assert "families" in tables
    assert "family_memberships" in tables
    assert "family_members" in tables
    assert "health_profiles" in tables
    assert "medical_conditions" in tables
    assert "allergy_profiles" in tables
    assert "drug_reaction_histories" in tables
    assert "emergency_contacts" in tables
    assert "medication_catalogs" in tables
    assert "family_medications" in tables
    assert "member_medications" in tables
    assert "prescriptions" in tables
    assert "prescription_items" in tables
    assert "medication_schedules" in tables
    assert "schedule_times" in tables
    assert "cabinets" in tables
    assert "compartments" in tables
    assert "cabinet_events" in tables
