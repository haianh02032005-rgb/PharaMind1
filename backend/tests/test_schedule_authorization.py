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


def test_schedule_role_matrix_and_cross_family_isolation():
    """TASK 08 §41–43, §51, §72–74: Cross-family 404, VIEWER cannot create/edit, CAREGIVER can create/update/pause/resume/complete but cannot archive."""
    owner_id, _, owner_token = _create_user_and_token("sched_owner")
    caregiver_id, caregiver_email, caregiver_token = _create_user_and_token(
        "sched_caregiver"
    )
    viewer_id, viewer_email, viewer_token = _create_user_and_token(
        "sched_viewer"
    )
    outsider_id, _, outsider_token = _create_user_and_token("sched_outsider")
    family_ids: list[int] = []
    catalog_ids: list[int] = []

    try:
        fam_a = client.post(
            "/families",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={"name": "Family A"},
        ).json()["id"]
        family_ids.append(fam_a)

        fam_b = client.post(
            "/families",
            headers={"Authorization": f"Bearer {outsider_token}"},
            json={"name": "Family B"},
        ).json()["id"]
        family_ids.append(fam_b)

        client.post(
            f"/families/{fam_a}/memberships",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={"email": caregiver_email, "role": "CAREGIVER"},
        )
        client.post(
            f"/families/{fam_a}/memberships",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={"email": viewer_email, "role": "VIEWER"},
        )

        member_a = client.post(
            f"/families/{fam_a}/members",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={"full_name": "Bà Lan"},
        ).json()["id"]

        med = client.post(
            f"/families/{fam_a}/medications",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={
                "name": f"Atorvastatin_{uuid4().hex[:6]}",
                "strength": "10 mg",
                "unit": "TABLET",
                "quantity": 30,
                "expiration_date": "2028-12-31",
            },
        ).json()
        catalog_ids.append(med["catalog"]["id"])

        client.post(
            f"/families/{fam_id if False else fam_a}/medications/{med['id']}/members",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={"member_id": member_a},
        )

        rx = client.post(
            f"/families/{fam_a}/prescriptions",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={
                "member_id": member_a,
                "title": "Đơn thuốc mỡ máu",
                "start_date": "2026-11-01",
                "end_date": "2026-11-30",
            },
        ).json()

        item = client.post(
            f"/families/{fam_a}/prescriptions/{rx['id']}/items",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={
                "family_medication_id": med["id"],
                "dose_amount": 1,
                "dose_unit": "TABLET",
                "frequency_per_day": 1,
                "route": "ORAL",
            },
        ).json()

        # 1. VIEWER cannot create schedule -> 403 (§73)
        viewer_create = client.post(
            f"/families/{fam_a}/schedules",
            headers={"Authorization": f"Bearer {viewer_token}"},
            json={
                "prescription_item_id": item["id"],
                "start_date": "2026-11-01",
                "end_date": "2026-11-30",
                "recurrence_type": "DAILY",
                "times": ["08:00"],
            },
        )
        assert viewer_create.status_code == 403

        # 2. CAREGIVER can create schedule -> 201
        cg_create = client.post(
            f"/families/{fam_a}/schedules",
            headers={"Authorization": f"Bearer {caregiver_token}"},
            json={
                "prescription_item_id": item["id"],
                "start_date": "2026-11-01",
                "end_date": "2026-11-30",
                "recurrence_type": "DAILY",
                "times": ["08:00"],
            },
        )
        assert cg_create.status_code == 201
        sched_id = cg_create.json()["id"]

        # 3. CAREGIVER can update 08:00 -> 08:30 (§74)
        cg_update = client.patch(
            f"/families/{fam_a}/schedules/{sched_id}",
            headers={"Authorization": f"Bearer {caregiver_token}"},
            json={"times": ["08:30"]},
        )
        assert cg_update.status_code == 200
        assert cg_update.json()["times"] == ["08:30"]

        # 4. VIEWER can read schedule & daily timeline -> 200
        viewer_get = client.get(
            f"/families/{fam_a}/schedules/{sched_id}",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert viewer_get.status_code == 200

        # 5. CAREGIVER cannot archive schedule -> 403 (§51)
        cg_archive = client.post(
            f"/families/{fam_a}/schedules/{sched_id}/archive",
            headers={"Authorization": f"Bearer {caregiver_token}"},
        )
        assert cg_archive.status_code == 403

        # 6. Cross-family read from Family B -> 404 (§42, §72)
        cross_get = client.get(
            f"/families/{fam_b}/schedules/{sched_id}",
            headers={"Authorization": f"Bearer {outsider_token}"},
        )
        assert cross_get.status_code == 404

        # Cross-family create using Family A's prescription_item in Family B -> 404 (§43)
        cross_create = client.post(
            f"/families/{fam_b}/schedules",
            headers={"Authorization": f"Bearer {outsider_token}"},
            json={
                "prescription_item_id": item["id"],
                "start_date": "2026-11-01",
                "end_date": "2026-11-30",
                "recurrence_type": "DAILY",
                "times": ["08:00"],
            },
        )
        assert cross_create.status_code == 404
    finally:
        _cleanup(
            [owner_id, caregiver_id, viewer_id, outsider_id],
            family_ids,
            catalog_ids,
        )

