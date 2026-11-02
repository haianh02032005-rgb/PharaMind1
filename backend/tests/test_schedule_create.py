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


def test_create_daily_and_prn_schedules_and_list():
    """TASK 08 §13–16, §22–24, §59, §66: Create DAILY and PRN schedules, derive member & medication, list & detail."""
    user_id, _, token = _create_user_and_token("sched_create")
    family_ids: list[int] = []
    catalog_ids: list[int] = []

    try:
        fam_id = client.post(
            "/families",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Schedule Create Family"},
        ).json()["id"]
        family_ids.append(fam_id)

        member_id = client.post(
            f"/families/{fam_id}/members",
            headers={"Authorization": f"Bearer {token}"},
            json={"full_name": "Nguyen Thi Lan", "relationship_label": "Mẹ"},
        ).json()["id"]

        med_daily = client.post(
            f"/families/{fam_id}/medications",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": f"Amlodipine_{uuid4().hex[:6]}",
                "strength": "5 mg",
                "unit": "TABLET",
                "quantity": 60,
                "expiration_date": "2027-12-31",
            },
        ).json()
        catalog_ids.append(med_daily["catalog"]["id"])

        med_prn = client.post(
            f"/families/{fam_id}/medications",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": f"Paracetamol_{uuid4().hex[:6]}",
                "strength": "500 mg",
                "unit": "TABLET",
                "quantity": 20,
                "expiration_date": "2027-12-31",
            },
        ).json()
        catalog_ids.append(med_prn["catalog"]["id"])

        for med in (med_daily, med_prn):
            assign_res = client.post(
                f"/families/{fam_id}/medications/{med['id']}/members",
                headers={"Authorization": f"Bearer {token}"},
                json={"member_id": member_id},
            )
            assert assign_res.status_code == 201

        rx = client.post(
            f"/families/{fam_id}/prescriptions",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "member_id": member_id,
                "title": "Đơn thuốc tháng 11",
                "start_date": "2026-11-01",
                "end_date": "2026-11-30",
            },
        ).json()

        item_daily = client.post(
            f"/families/{fam_id}/prescriptions/{rx['id']}/items",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "family_medication_id": med_daily["id"],
                "dose_amount": 1,
                "dose_unit": "TABLET",
                "frequency_per_day": 1,
                "route": "ORAL",
                "instructions": "Uống sau ăn sáng",
            },
        ).json()

        item_prn = client.post(
            f"/families/{fam_id}/prescriptions/{rx['id']}/items",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "family_medication_id": med_prn["id"],
                "dose_amount": 1,
                "dose_unit": "TABLET",
                "frequency_text": "Khi đau đầu",
                "route": "ORAL",
            },
        ).json()

        # 1. Create DAILY schedule (§59)
        create_res = client.post(
            f"/families/{fam_id}/schedules",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "prescription_item_id": item_daily["id"],
                "start_date": "2026-11-01",
                "end_date": "2026-11-30",
                "recurrence_type": "DAILY",
                "times": ["08:00"],
                "reminder_enabled": True,
                "reminder_before_minutes": 10,
                "grace_period_minutes": 30,
                "notes": "Uống sau ăn sáng",
            },
        )
        assert create_res.status_code == 201
        sched = create_res.json()
        assert sched["family_id"] == fam_id
        assert sched["member_id"] == member_id
        assert sched["family_medication_id"] == med_daily["id"]
        assert sched["member"]["full_name"] == "Nguyen Thi Lan"
        assert sched["medication"]["id"] == med_daily["id"]
        assert sched["dose_amount"] == 1.0
        assert sched["dose_unit"] == "TABLET"
        assert sched["times"] == ["08:00"]
        assert sched["status"] == "ACTIVE"

        # 2. Create PRN schedule with empty times (§66)
        prn_res = client.post(
            f"/families/{fam_id}/schedules",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "prescription_item_id": item_prn["id"],
                "start_date": "2026-11-01",
                "end_date": "2026-11-30",
                "recurrence_type": "PRN",
                "times": [],
                "notes": "Dùng khi đau",
            },
        )
        assert prn_res.status_code == 201
        prn_sched = prn_res.json()
        assert prn_sched["recurrence_type"] == "PRN"
        assert prn_sched["times"] == []

        # 3. Get schedule detail & list schedules (§22–24)
        detail_res = client.get(
            f"/families/{fam_id}/schedules/{sched['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert detail_res.status_code == 200
        assert detail_res.json()["id"] == sched["id"]

        list_res = client.get(
            f"/families/{fam_id}/schedules?member_id={member_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert list_res.status_code == 200
        assert len(list_res.json()["items"]) == 2

        mem_list_res = client.get(
            f"/families/{fam_id}/members/{member_id}/schedules",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert mem_list_res.status_code == 200
        assert len(mem_list_res.json()["items"]) == 2
    finally:
        _cleanup([user_id], family_ids, catalog_ids)

