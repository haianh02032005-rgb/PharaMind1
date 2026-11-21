from importlib import import_module

from alembic.operations import Operations
from alembic.runtime.migration import MigrationContext
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.api.dependencies import get_db
from backend.app.main import app


def test_curated_pharmacies_are_seeded_and_served_from_database():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    migration = import_module(
        "backend.alembic.versions.d382f5e9c716_add_curated_pharmacies"
    )
    with engine.begin() as connection:
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        assert connection.execute(
            text("SELECT COUNT(*) FROM curated_pharmacies")
        ).scalar_one() == 6

    def override_db():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_db] = override_db
    try:
        response = TestClient(app).get("/pharmacies/curated")
        assert response.status_code == 200
        stores = response.json()
        assert len(stores) == 6
        assert all(store["phone"] == "1800 6928" for store in stores)
        assert all(store["phone_kind"] == "chain_hotline" for store in stores)
        assert all(store["source_url"].startswith("https://nhathuoclongchau.com.vn/") for store in stores)
    finally:
        app.dependency_overrides.pop(get_db, None)
        engine.dispose()
