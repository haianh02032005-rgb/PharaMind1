from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import delete

from backend.app.db.session import SessionLocal
from backend.app.main import app
from backend.app.models.family import Family
from backend.app.models.medication_catalog import MedicationCatalog
from backend.app.models.medication_schedule import MedicationSchedule
from backend.app.models.prescription import Prescription
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


def _cleanup(
    user_ids: list[int],
    family_ids: list[int],
    catalog_ids: list[int],
) -> None:
    with SessionLocal() as session:
        if family_ids:
            session.execute(
                delete(MedicationSchedule).where(
                    MedicationSchedule.family_id.in_(family_ids)
                )
            )
            session.execute(
                delete(Prescription).where(
                    Prescription.family_id.in_(family_ids)
                )
            )
            session.execute(delete(Family).where(Family.id.in_(family_ids)))
        if catalog_ids:
            session.execute(
                delete(MedicationCatalog).where(
                    MedicationCatalog.id.in_(catalog_ids)
                )
            )
        if user_ids:
            session.execute(delete(User).where(User.id.in_(user_ids)))
        session.commit()


def test_daily_schedule_timeline_sorted_and_excludes_paused():
    """TASK 08 §32, §33, §67, §70: Daily timeline returns items sorted ascending by time and excludes PAUSED schedules."""
    user_id, _, token = _create_user_and_token("sched_daily")
    family_ids: list[int] = []
    catalog_ids: list[int] = []

    try:
        fam_id = client.post(
            "/families",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Daily Timeline Family"},
        ).json()["id"]
        family_ids.append(fam_id)

        member_id = client.post(
            f"/families/{fam_id}/members",
            headers={"Authorization": f"Bearer {token}"},
            json={"full_name": "Bà Lan"},
        ).json()["id"]

        med_1 = client.post(
            f"/families/{fam_id}/medications",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": f"Amlodipine_{uuid4().hex[:6]}",
                "strength": "5 mg",
                "unit": "TABLET",
                "quantity": 30,
                "expiration_date": "2028-12-31",
            },
        ).json()
        catalog_ids.append(med_1["catalog"]["id"])

        med_2 = client.post(
            f"/families/{fam_id}/medications",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": f"VitaminD_{uuid4().hex[:6]}",
                "strength": "1000 IU",
                "unit": "CAPSULE",
                "quantity": 30,
                "expiration_date": "2028-12-31",
            },
        ).json()
        catalog_ids.append(med_2["catalog"]["id"])

        for med in (med_1, med_2):
            client.post(
                f"/families/{fam_id}/medications/{med['id']}/members",
                headers={"Authorization": f"Bearer {token}"},
                json={"member_id": member_id},
            )

        rx = client.post(
            f"/families/{fam_id}/prescriptions",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "member_id": member_id,
                "title": "Đơn thuốc tổng hợp",
                "start_date": "2026-11-01",
                "end_date": "2026-11-30",
            },
        ).json()

        item_1 = client.post(
            f"/families/{fam_id}/prescriptions/{rx['id']}/items",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "family_medication_id": med_1["id"],
                "dose_amount": 1,
                "dose_unit": "TABLET",
                "frequency_per_day": 2,
                "route": "ORAL",
            },
        ).json()

        item_2 = client.post(
            f"/families/{fam_id}/prescriptions/{rx['id']}/items",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "family_medication_id": med_2["id"],
                "dose_amount": 1,
                "dose_unit": "CAPSULE",
                "frequency_per_day": 1,
                "route": "ORAL",
            },
        ).json()

        # Schedule 1: 08:00 and 20:00
        s1 = client.post(
            f"/families/{fam_id}/schedules",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "prescription_item_id": item_1["id"],
                "start_date": "2026-11-01",
                "end_date": "2026-11-30",
                "recurrence_type": "DAILY",
                "times": ["20:00", "08:00"],
            },
        ).json()

        # Schedule 2: 12:00
        s2 = client.post(
            f"/families/{fam_id}/schedules",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "prescription_item_id": item_2["id"],
                "start_date": "2026-11-01",
                "end_date": "2026-11-30",
                "recurrence_type": "DAILY",
                "times": ["12:00"],
            },
        ).json()

        # Query daily schedule for 2026-11-05 -> [08:00, 12:00, 20:00] (§67)
        day_res = client.get(
            f"/families/{fam_id}/members/{member_id}/schedule-day?date=2026-11-05",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert day_res.status_code == 200
        day_data = day_res.json()
        assert day_data["date"] == "2026-11-05"
        assert [i["time"] for i in day_data["items"]] == [
            "08:00",
            "12:00",
            "20:00",
        ]
        assert all(i["status"] == "SCHEDULED" for i in day_data["items"])

        # Pause Schedule 2 (12:00) -> excluded from daily timeline (§70)
        client.post(
            f"/families/{fam_id}/schedules/{s2['id']}/pause",
            headers={"Authorization": f"Bearer {token}"},
        )

        day_res_after_pause = client.get(
            f"/families/{fam_id}/members/{member_id}/schedule-day?date=2026-11-05",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert day_res_after_pause.status_code == 200
        assert [i["time"] for i in day_res_after_pause.json()["items"]] == [
            "08:00",
            "20:00",
        ]
        assert all(
            i["schedule_id"] == s1["id"]
            for i in day_res_after_pause.json()["items"]
        )
    finally:
        _cleanup([user_id], family_ids, catalog_ids)

