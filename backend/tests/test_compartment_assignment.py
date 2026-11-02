from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import delete

from backend.app.db.session import SessionLocal
from backend.app.main import app
from backend.app.models.cabinet import Cabinet
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
            session.execute(
                delete(Cabinet).where(Cabinet.family_id.in_(family_ids))
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


def test_compartment_assign_unassign_duplicate_and_schedule_aware_detail():
    """TASK 09 §29–33, §41–42, §81–83: Assign medication, reject duplicate & cross-family & archived/expired, unassign, and schedule-aware compartment detail."""
    user_a_id, _, token_a = _create_user_and_token("comp_assign_a")
    user_b_id, _, token_b = _create_user_and_token("comp_assign_b")
    family_ids: list[int] = []
    catalog_ids: list[int] = []

    try:
        fam_a = client.post(
            "/families",
            headers={"Authorization": f"Bearer {token_a}"},
            json={"name": "Family A"},
        ).json()["id"]
        family_ids.append(fam_a)

        fam_b = client.post(
            "/families",
            headers={"Authorization": f"Bearer {token_b}"},
            json={"name": "Family B"},
        ).json()["id"]
        family_ids.append(fam_b)

        cab_a = client.post(
            f"/families/{fam_a}/cabinets",
            headers={"Authorization": f"Bearer {token_a}"},
            json={
                "name": "Tủ Family A",
                "device_code": f"PM-CAB-{uuid4().hex[:8].upper()}",
            },
        ).json()["id"]

        member_a = client.post(
            f"/families/{fam_a}/members",
            headers={"Authorization": f"Bearer {token_a}"},
            json={"full_name": "Nguyen Thi Lan"},
        ).json()["id"]

        med_a = client.post(
            f"/families/{fam_a}/medications",
            headers={"Authorization": f"Bearer {token_a}"},
            json={
                "name": f"Amlodipine_{uuid4().hex[:6]}",
                "strength": "5 mg",
                "dosage_form": "TABLET",
                "quantity": 20,
                "unit": "TABLET",
                "expiration_date": "2028-05-31",
            },
        ).json()
        catalog_ids.append(med_a["catalog"]["id"])

        med_b = client.post(
            f"/families/{fam_b}/medications",
            headers={"Authorization": f"Bearer {token_b}"},
            json={
                "name": f"OtherFamMed_{uuid4().hex[:6]}",
                "quantity": 10,
                "unit": "TABLET",
            },
        ).json()
        catalog_ids.append(med_b["catalog"]["id"])

        # Create schedule for med_a so Compartment Detail includes next_dose (§42)
        client.post(
            f"/families/{fam_a}/medications/{med_a['id']}/members",
            headers={"Authorization": f"Bearer {token_a}"},
            json={"member_id": member_a},
        )
        rx = client.post(
            f"/families/{fam_a}/prescriptions",
            headers={"Authorization": f"Bearer {token_a}"},
            json={
                "member_id": member_a,
                "title": "Đơn huyết áp",
                "start_date": "2026-01-01",
                "end_date": "2028-12-31",
            },
        ).json()
        rx_item = client.post(
            f"/families/{fam_a}/prescriptions/{rx['id']}/items",
            headers={"Authorization": f"Bearer {token_a}"},
            json={
                "family_medication_id": med_a["id"],
                "dose_amount": 1,
                "dose_unit": "TABLET",
                "frequency_per_day": 1,
            },
        ).json()
        client.post(
            f"/families/{fam_a}/schedules",
            headers={"Authorization": f"Bearer {token_a}"},
            json={
                "prescription_item_id": rx_item["id"],
                "start_date": "2026-01-01",
                "end_date": "2028-12-31",
                "recurrence_type": "DAILY",
                "times": ["20:00"],
            },
        )

        # 1. Assign med_a to compartment 8 -> status AVAILABLE (§81)
        assign_res = client.put(
            f"/families/{fam_a}/cabinets/{cab_a}/compartments/8/medication",
            headers={"Authorization": f"Bearer {token_a}"},
            json={"family_medication_id": med_a["id"]},
        )
        assert assign_res.status_code == 200
        comp_8 = assign_res.json()
        assert comp_8["position"] == 8
        assert comp_8["object_id"] == "drawer_08"
        assert comp_8["status"] == "AVAILABLE"
        assert comp_8["family_medication_id"] == med_a["id"]
        assert comp_8["medication"]["id"] == med_a["id"]

        # 2. Duplicate assignment to compartment 2 -> 409 (§82)
        dup_res = client.put(
            f"/families/{fam_a}/cabinets/{cab_a}/compartments/2/medication",
            headers={"Authorization": f"Bearer {token_a}"},
            json={"family_medication_id": med_a["id"]},
        )
        assert dup_res.status_code == 409

        # 3. Cross-family medication assignment -> 404 (§83)
        cross_res = client.put(
            f"/families/{fam_a}/cabinets/{cab_a}/compartments/2/medication",
            headers={"Authorization": f"Bearer {token_a}"},
            json={"family_medication_id": med_b["id"]},
        )
        assert cross_res.status_code == 404

        # 4. Compartment detail includes medication + next_dose (§41, §42)
        detail_res = client.get(
            f"/families/{fam_a}/cabinets/{cab_a}/compartments/8",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert detail_res.status_code == 200
        detail = detail_res.json()
        assert detail["position"] == 8
        assert detail["medication"]["id"] == med_a["id"]
        assert detail["next_dose"] is not None
        assert detail["next_dose"]["time"] == "20:00"
        assert detail["next_dose"]["member"]["full_name"] == "Nguyen Thi Lan"

        # 5. Unassign medication from compartment 8 -> status EMPTY (§31)
        unassign_res = client.delete(
            f"/families/{fam_a}/cabinets/{cab_a}/compartments/8/medication",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert unassign_res.status_code == 200
        assert unassign_res.json()["family_medication_id"] is None
        assert unassign_res.json()["status"] == "EMPTY"
    finally:
        _cleanup([user_a_id, user_b_id], family_ids, catalog_ids)

