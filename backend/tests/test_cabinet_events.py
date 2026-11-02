from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import delete

from backend.app.db.session import SessionLocal
from backend.app.main import app
from backend.app.models.cabinet import Cabinet
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
            session.execute(
                delete(Cabinet).where(Cabinet.family_id.in_(family_ids))
            )
            session.execute(delete(Family).where(Family.id.in_(family_ids)))
        if user_ids:
            session.execute(delete(User).where(User.id.in_(user_ids)))
        session.commit()


def test_cabinet_events_logged_and_no_medication_taken_event():
    """TASK 09 §56–59, §84, §86, §87, §89: Event history records CABINET_ONLINE, COMPARTMENT_OPEN, COMPARTMENT_CLOSE, CABINET_OFFLINE; never logs MEDICATION_TAKEN."""
    user_id, _, token = _create_user_and_token("cab_events")
    family_ids: list[int] = []

    try:
        fam_id = client.post(
            "/families",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Events Family"},
        ).json()["id"]
        family_ids.append(fam_id)

        cab_id = client.post(
            f"/families/{fam_id}/cabinets",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "Tủ sự kiện",
                "device_code": f"PM-CAB-{uuid4().hex[:8].upper()}",
            },
        ).json()["id"]

        client.post(
            f"/families/{fam_id}/cabinets/{cab_id}/simulator/online",
            headers={"Authorization": f"Bearer {token}"},
        )
        client.post(
            f"/families/{fam_id}/cabinets/{cab_id}/compartments/8/open",
            headers={"Authorization": f"Bearer {token}"},
        )
        client.post(
            f"/families/{fam_id}/cabinets/{cab_id}/compartments/8/close",
            headers={"Authorization": f"Bearer {token}"},
        )
        client.post(
            f"/families/{fam_id}/cabinets/{cab_id}/simulator/offline",
            headers={"Authorization": f"Bearer {token}"},
        )

        events_res = client.get(
            f"/families/{fam_id}/cabinets/{cab_id}/events",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert events_res.status_code == 200
        events = events_res.json()["items"]
        event_types = [e["event_type"] for e in events]
        assert "CABINET_ONLINE" in event_types
        assert "COMPARTMENT_OPEN" in event_types
        assert "COMPARTMENT_CLOSE" in event_types
        assert "CABINET_OFFLINE" in event_types
        assert "MEDICATION_TAKEN" not in event_types
        assert "USER_CONFIRMED" not in event_types

        # Filter by event_type=COMPARTMENT_OPEN
        open_events = client.get(
            f"/families/{fam_id}/cabinets/{cab_id}/events?event_type=COMPARTMENT_OPEN",
            headers={"Authorization": f"Bearer {token}"},
        ).json()["items"]
        assert len(open_events) == 1
        assert open_events[0]["compartment_position"] == 8
    finally:
        _cleanup([user_id], family_ids)

