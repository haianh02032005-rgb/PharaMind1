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


def test_next_dose_same_day_next_day_and_paused_excluded():
    """TASK 08 §34–36, §68–70: Next dose at 10:00 returns 12:00; at 22:00 returns next day 08:00; paused schedules excluded."""
    user_id, _, token = _create_user_and_token("sched_next")
    family_ids: list[int] = []
    catalog_ids: list[int] = []

    try:
        fam_id = client.post(
            "/families",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Next Dose Family"},
        ).json()["id"]
        family_ids.append(fam_id)

        member_id = client.post(
            f"/families/{fam_id}/members",
            headers={"Authorization": f"Bearer {token}"},
            json={"full_name": "Bà Lan"},
        ).json()["id"]

        med = client.post(
            f"/families/{fam_id}/medications",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": f"Losartan_{uuid4().hex[:6]}",
                "strength": "50 mg",
                "unit": "TABLET",
                "quantity": 60,
                "expiration_date": "2028-12-31",
            },
        ).json()
        catalog_ids.append(med["catalog"]["id"])

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
                "title": "Đơn thuốc huyết áp",
                "start_date": "2026-11-01",
                "end_date": "2026-11-30",
            },
        ).json()

        item = client.post(
            f"/families/{fam_id}/prescriptions/{rx['id']}/items",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "family_medication_id": med["id"],
                "dose_amount": 1,
                "dose_unit": "TABLET",
                "frequency_per_day": 3,
                "route": "ORAL",
            },
        ).json()

        sched = client.post(
            f"/families/{fam_id}/schedules",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "prescription_item_id": item["id"],
                "start_date": "2026-11-01",
                "end_date": "2026-11-30",
                "recurrence_type": "DAILY",
                "times": ["08:00", "12:00", "20:00"],
            },
        ).json()

        # 1. Current time 10:00 on 2026-11-01 -> next dose is 12:00 today (§68)
        res_10 = client.get(
            f"/families/{fam_id}/members/{member_id}/next-dose?now=2026-11-01T10:00:00",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res_10.status_code == 200
        d10 = res_10.json()
        assert d10["schedule_id"] == sched["id"]
        assert d10["date"] == "2026-11-01"
        assert d10["time"] == "12:00"
        assert d10["medication"]["id"] == med["id"]
        assert d10["dose_amount"] == 1.0
        assert d10["dose_unit"] == "TABLET"

        # 2. Current time 22:00 on 2026-11-01 -> next dose is 08:00 on 2026-11-02 (§69)
        res_22 = client.get(
            f"/families/{fam_id}/members/{member_id}/next-dose?now=2026-11-01T22:00:00",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res_22.status_code == 200
        d22 = res_22.json()
        assert d22["schedule_id"] == sched["id"]
        assert d22["date"] == "2026-11-02"
        assert d22["time"] == "08:00"

        # 3. Pause schedule -> next-dose returns null schedule_id (§70)
        client.post(
            f"/families/{fam_id}/schedules/{sched['id']}/pause",
            headers={"Authorization": f"Bearer {token}"},
        )
        res_paused = client.get(
            f"/families/{fam_id}/members/{member_id}/next-dose?now=2026-11-01T10:00:00",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res_paused.status_code == 200
        assert res_paused.json()["schedule_id"] is None
    finally:
        _cleanup([user_id], family_ids, catalog_ids)

