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


def test_schedule_validation_rules():
    """TASK 08 §17–21, §48–49, §60–65: Frequency mismatch, duplicate time, invalid time, invalid date range, prescription date bounds, expired medication."""
    user_id, _, token = _create_user_and_token("sched_val")
    family_ids: list[int] = []
    catalog_ids: list[int] = []

    try:
        fam_id = client.post(
            "/families",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Validation Family"},
        ).json()["id"]
        family_ids.append(fam_id)

        member_id = client.post(
            f"/families/{fam_id}/members",
            headers={"Authorization": f"Bearer {token}"},
            json={"full_name": "Bà Lan"},
        ).json()["id"]

        med_valid = client.post(
            f"/families/{fam_id}/medications",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": f"ValidMed_{uuid4().hex[:6]}",
                "strength": "10 mg",
                "unit": "TABLET",
                "quantity": 30,
                "expiration_date": "2028-12-31",
            },
        ).json()
        catalog_ids.append(med_valid["catalog"]["id"])

        med_expired = client.post(
            f"/families/{fam_id}/medications",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": f"ExpiredMed_{uuid4().hex[:6]}",
                "strength": "10 mg",
                "unit": "TABLET",
                "quantity": 10,
                "expiration_date": "2020-01-01",
            },
        ).json()
        catalog_ids.append(med_expired["catalog"]["id"])

        for med in (med_valid, med_expired):
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
                "title": "Đơn thuốc chuẩn",
                "start_date": "2026-11-10",
                "end_date": "2026-11-30",
            },
        ).json()

        item_2x = client.post(
            f"/families/{fam_id}/prescriptions/{rx['id']}/items",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "family_medication_id": med_valid["id"],
                "dose_amount": 1,
                "dose_unit": "TABLET",
                "frequency_per_day": 2,
                "route": "ORAL",
            },
        ).json()

        item_exp = client.post(
            f"/families/{fam_id}/prescriptions/{rx['id']}/items",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "family_medication_id": med_expired["id"],
                "dose_amount": 1,
                "dose_unit": "TABLET",
                "frequency_per_day": 1,
                "route": "ORAL",
            },
        ).json()

        # 1. Frequency mismatch: frequency_per_day=2, times=["08:00"] -> 422 (§60)
        freq_res = client.post(
            f"/families/{fam_id}/schedules",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "prescription_item_id": item_2x["id"],
                "start_date": "2026-11-10",
                "end_date": "2026-11-30",
                "recurrence_type": "DAILY",
                "times": ["08:00"],
            },
        )
        assert freq_res.status_code == 422

        # 2. Duplicate time: ["08:00", "08:00"] -> 422 (§61)
        dup_res = client.post(
            f"/families/{fam_id}/schedules",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "prescription_item_id": item_2x["id"],
                "start_date": "2026-11-10",
                "end_date": "2026-11-30",
                "recurrence_type": "DAILY",
                "times": ["08:00", "08:00"],
            },
        )
        assert dup_res.status_code == 422

        # 3. Invalid time: "25:00" -> 422 (§62)
        inv_time_res = client.post(
            f"/families/{fam_id}/schedules",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "prescription_item_id": item_2x["id"],
                "start_date": "2026-11-10",
                "end_date": "2026-11-30",
                "recurrence_type": "DAILY",
                "times": ["08:00", "25:00"],
            },
        )
        assert inv_time_res.status_code == 422

        # 4. Invalid date range: start_date > end_date -> 422 (§63)
        inv_date_res = client.post(
            f"/families/{fam_id}/schedules",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "prescription_item_id": item_2x["id"],
                "start_date": "2026-11-25",
                "end_date": "2026-11-15",
                "recurrence_type": "DAILY",
                "times": ["08:00", "20:00"],
            },
        )
        assert inv_date_res.status_code == 422

        # 5. Schedule before prescription start (01/11 < 10/11) -> 422 (§64)
        before_rx_res = client.post(
            f"/families/{fam_id}/schedules",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "prescription_item_id": item_2x["id"],
                "start_date": "2026-11-01",
                "end_date": "2026-11-30",
                "recurrence_type": "DAILY",
                "times": ["08:00", "20:00"],
            },
        )
        assert before_rx_res.status_code == 422

        # 6. Schedule after prescription end (10/12 > 30/11) -> 422 (§65)
        after_rx_res = client.post(
            f"/families/{fam_id}/schedules",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "prescription_item_id": item_2x["id"],
                "start_date": "2026-11-10",
                "end_date": "2026-12-10",
                "recurrence_type": "DAILY",
                "times": ["08:00", "20:00"],
            },
        )
        assert after_rx_res.status_code == 422

        # 7. Expired medication cannot be used to create new schedule -> 409 (§49)
        exp_res = client.post(
            f"/families/{fam_id}/schedules",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "prescription_item_id": item_exp["id"],
                "start_date": "2026-11-10",
                "end_date": "2026-11-30",
                "recurrence_type": "DAILY",
                "times": ["08:00"],
            },
        )
        assert exp_res.status_code == 409
    finally:
        _cleanup([user_id], family_ids, catalog_ids)

