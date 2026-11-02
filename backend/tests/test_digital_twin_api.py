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


def test_digital_twin_summary_endpoint_with_schedules_warnings_and_allergies():
    """TASK 10 §29–32, §53–56: Digital Twin summary returns 9 compartments, assigned medications, member schedules, next_dose_position, warnings, and allergy alerts."""
    user_id, _, token = _create_user_and_token("dt_summary")
    family_ids: list[int] = []
    catalog_ids: list[int] = []

    try:
        fam_id = client.post(
            "/families",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Gia đình Nguyễn Văn An"},
        ).json()["id"]
        family_ids.append(fam_id)

        cab_id = client.post(
            f"/families/{fam_id}/cabinets",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "Tủ thuốc phòng khách",
                "device_code": f"PM-DT-{uuid4().hex[:8].upper()}",
            },
        ).json()["id"]

        # Create 2 family members
        member_lan = client.post(
            f"/families/{fam_id}/members",
            headers={"Authorization": f"Bearer {token}"},
            json={"full_name": "Nguyễn Thị Lan", "relationship_label": "Mẹ"},
        ).json()["id"]

        member_an = client.post(
            f"/families/{fam_id}/members",
            headers={"Authorization": f"Bearer {token}"},
            json={"full_name": "Nguyễn Văn An", "relationship_label": "Bố"},
        ).json()["id"]

        # Add an allergy for member_lan to Penicillin / Amoxicillin
        allergy_res = client.post(
            f"/families/{fam_id}/members/{member_lan}/allergies",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "allergen": "Amoxicillin",
                "allergy_type": "DRUG",
                "severity": "SEVERE",
                "reaction_description": "Nổi mẩn đỏ và khó thở",
            },
        )
        assert allergy_res.status_code == 201

        # Create Medication 1: Paracetamol (low stock)
        med_para = client.post(
            f"/families/{fam_id}/medications",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": f"Paracetamol_{uuid4().hex[:6]}",
                "active_ingredient": "Paracetamol",
                "strength": "500mg",
                "dosage_form": "TABLET",
                "quantity": 4,
                "unit": "TABLET",
                "low_stock_threshold": 5,
                "expiration_date": "2028-06-30",
            },
        ).json()
        catalog_ids.append(med_para["catalog"]["id"])

        # Create Medication 2: Amoxicillin (triggers allergy alert for member_lan)
        med_amox = client.post(
            f"/families/{fam_id}/medications",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": f"Amoxicillin_{uuid4().hex[:6]}",
                "active_ingredient": "Amoxicillin",
                "strength": "500mg",
                "dosage_form": "CAPSULE",
                "quantity": 18,
                "unit": "CAPSULE",
                "expiration_date": "2028-08-30",
            },
        ).json()
        catalog_ids.append(med_amox["catalog"]["id"])

        # Link members & create schedule on med_para for member_lan at 20:00
        client.post(
            f"/families/{fam_id}/medications/{med_para['id']}/members",
            headers={"Authorization": f"Bearer {token}"},
            json={"member_id": member_lan},
        )
        client.post(
            f"/families/{fam_id}/medications/{med_amox['id']}/members",
            headers={"Authorization": f"Bearer {token}"},
            json={"member_id": member_lan},
        )

        rx = client.post(
            f"/families/{fam_id}/prescriptions",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "member_id": member_lan,
                "title": "Đơn thuốc cảm sốt",
                "start_date": "2026-01-01",
                "end_date": "2028-12-31",
            },
        ).json()
        rx_item = client.post(
            f"/families/{fam_id}/prescriptions/{rx['id']}/items",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "family_medication_id": med_para["id"],
                "dose_amount": 1,
                "dose_unit": "TABLET",
                "frequency_per_day": 2,
                "instructions": "Uống sau ăn no",
            },
        ).json()
        client.post(
            f"/families/{fam_id}/schedules",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "prescription_item_id": rx_item["id"],
                "start_date": "2026-01-01",
                "end_date": "2028-12-31",
                "recurrence_type": "DAILY",
                "times": ["08:00", "20:00"],
            },
        )

        # Assign med_para -> compartment 1, med_amox -> compartment 8
        client.put(
            f"/families/{fam_id}/cabinets/{cab_id}/compartments/1/medication",
            headers={"Authorization": f"Bearer {token}"},
            json={"family_medication_id": med_para["id"]},
        )
        client.put(
            f"/families/{fam_id}/cabinets/{cab_id}/compartments/8/medication",
            headers={"Authorization": f"Bearer {token}"},
            json={"family_medication_id": med_amox["id"]},
        )

        # Query Digital Twin summary
        dt_res = client.get(
            f"/families/{fam_id}/cabinets/{cab_id}/digital-twin",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert dt_res.status_code == 200
        data = dt_res.json()

        assert data["cabinet"]["id"] == cab_id
        assert data["cabinet"]["name"] == "Tủ thuốc phòng khách"
        assert data["next_dose_position"] == 1
        assert data["next_dose"] is not None
        assert len(data["compartments"]) == 9

        comp_1 = data["compartments"][0]
        assert comp_1["position"] == 1
        assert comp_1["object_id"] == "drawer_01"
        assert comp_1["medication"]["id"] == med_para["id"]
        assert "LOW_STOCK" in comp_1["warnings"]
        assert len(comp_1["members"]) == 1
        assert comp_1["members"][0]["full_name"] == "Nguyễn Thị Lan"
        assert comp_1["members"][0]["schedules"][0]["times"] == ["08:00", "20:00"]

        comp_8 = data["compartments"][7]
        assert comp_8["position"] == 8
        assert comp_8["object_id"] == "drawer_08"
        assert comp_8["medication"]["id"] == med_amox["id"]
        assert "ALLERGY_RISK" in comp_8["warnings"]
        assert len(comp_8["allergy_alerts"]) == 1
        assert comp_8["allergy_alerts"][0]["substance"] == "Amoxicillin"

        # Filter by member_an (who has no schedules on med_para)
        dt_filtered = client.get(
            f"/families/{fam_id}/cabinets/{cab_id}/digital-twin?member_id={member_an}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert dt_filtered.status_code == 200
        filtered_data = dt_filtered.json()
        assert filtered_data["next_dose_position"] is None

        # Test Compartment Reveal Endpoint (FEATURE_DRAWER_OPEN_CAPSULE_REVEAL §30)
        reveal_1 = client.get(
            f"/families/{fam_id}/cabinets/{cab_id}/compartments/1/reveal",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert reveal_1.status_code == 200
        r1 = reveal_1.json()
        assert r1["position"] == 1
        assert r1["object_id"] == "drawer_01"
        assert r1["is_next_dose"] is True
        assert r1["medication"]["id"] == med_para["id"]
        assert len(r1["members"]) == 1
        assert r1["members"][0]["full_name"] == "Nguyễn Thị Lan"
        assert r1["members"][0]["dose_amount"] == 1
        assert r1["members"][0]["next_schedule"] is not None

        reveal_8 = client.get(
            f"/families/{fam_id}/cabinets/{cab_id}/compartments/8/reveal",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert reveal_8.status_code == 200
        r8 = reveal_8.json()
        assert r8["position"] == 8
        assert any(w["type"] == "ALLERGY_WARNING" for w in r8["warnings"])

        reveal_empty = client.get(
            f"/families/{fam_id}/cabinets/{cab_id}/compartments/3/reveal",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert reveal_empty.status_code == 200
        assert reveal_empty.json()["medication"] is None
        assert reveal_empty.json()["members"] == []
    finally:
        _cleanup([user_id], family_ids, catalog_ids)
