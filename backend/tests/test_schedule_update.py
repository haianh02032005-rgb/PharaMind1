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


def test_update_pause_resume_complete_archive_restore_schedule():
    """TASK 08 §25–31, §71: Update schedule times atomically, pause, resume, complete, archive, restore (to PAUSED)."""
    user_id, _, token = _create_user_and_token("sched_update")
    family_ids: list[int] = []
    catalog_ids: list[int] = []

    try:
        fam_id = client.post(
            "/families",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Schedule Lifecycle Family"},
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
                "name": f"Metformin_{uuid4().hex[:6]}",
                "strength": "500 mg",
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
                "title": "Đơn thuốc đường huyết",
                "start_date": "2026-01-01",
                "end_date": "2028-12-31",
            },
        ).json()

        item = client.post(
            f"/families/{fam_id}/prescriptions/{rx['id']}/items",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "family_medication_id": med["id"],
                "dose_amount": 1,
                "dose_unit": "TABLET",
                "frequency_per_day": 2,
                "route": "ORAL",
            },
        ).json()

        sched = client.post(
            f"/families/{fam_id}/schedules",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "prescription_item_id": item["id"],
                "start_date": "2026-11-01",
                "end_date": "2027-11-30",
                "recurrence_type": "DAILY",
                "times": ["08:00", "20:00"],
            },
        ).json()
        sched_id = sched["id"]

        # 1. Update times & notes (§25, §26)
        patch_res = client.patch(
            f"/families/{fam_id}/schedules/{sched_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "times": ["08:30", "20:30"],
                "reminder_before_minutes": 15,
                "notes": "Đã chỉnh giờ uống",
            },
        )
        assert patch_res.status_code == 200
        assert patch_res.json()["times"] == ["08:30", "20:30"]
        assert patch_res.json()["reminder_before_minutes"] == 15
        assert patch_res.json()["notes"] == "Đã chỉnh giờ uống"

        # 2. Pause -> PAUSED (§27)
        pause_res = client.post(
            f"/families/{fam_id}/schedules/{sched_id}/pause",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert pause_res.status_code == 200
        assert pause_res.json()["status"] == "PAUSED"

        # 3. Resume -> ACTIVE (§28)
        resume_res = client.post(
            f"/families/{fam_id}/schedules/{sched_id}/resume",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resume_res.status_code == 200
        assert resume_res.json()["status"] == "ACTIVE"

        # 4. Archive -> hidden by default, shown with include_archived=true (§30, §71)
        arch_res = client.post(
            f"/families/{fam_id}/schedules/{sched_id}/archive",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert arch_res.status_code == 200
        assert arch_res.json()["status"] == "ARCHIVED"

        default_list = client.get(
            f"/families/{fam_id}/schedules",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert default_list.status_code == 200
        assert default_list.json()["items"] == []

        inc_list = client.get(
            f"/families/{fam_id}/schedules?include_archived=true",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert inc_list.status_code == 200
        assert [s["id"] for s in inc_list.json()["items"]] == [sched_id]

        # 5. Restore -> restores to PAUSED (§31)
        rest_res = client.post(
            f"/families/{fam_id}/schedules/{sched_id}/restore",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert rest_res.status_code == 200
        assert rest_res.json()["status"] == "PAUSED"

        # 6. Complete -> COMPLETED (§29)
        comp_res = client.post(
            f"/families/{fam_id}/schedules/{sched_id}/complete",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert comp_res.status_code == 200
        assert comp_res.json()["status"] == "COMPLETED"
    finally:
        _cleanup([user_id], family_ids, catalog_ids)

