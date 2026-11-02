from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import delete

from backend.app.db.session import SessionLocal
from backend.app.main import app
from backend.app.models.family import Family
from backend.app.models.medication_catalog import MedicationCatalog
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


def test_prescription_date_dose_and_frequency_validation():
    """TASK 07 §23, §56–58: start_date > end_date, negative dose_amount, negative frequency_per_day rejected (422); null frequency_per_day with frequency_text allowed."""
    owner_id, _, token = _create_user_and_token("rx_val_owner")
    family_ids: list[int] = []
    catalog_ids: list[int] = []

    try:
        fam_id = client.post(
            "/families",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Family Validation"},
        ).json()["id"]
        family_ids.append(fam_id)

        mem_id = client.post(
            f"/families/{fam_id}/members",
            headers={"Authorization": f"Bearer {token}"},
            json={"full_name": "Bà Lan"},
        ).json()["id"]

        med = client.post(
            f"/families/{fam_id}/medications",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": f"Paracetamol-{uuid4().hex[:6]}",
                "quantity": 20,
                "unit": "TABLET",
            },
        ).json()
        med_id = med["id"]
        catalog_ids.append(med["catalog"]["id"])

        client.post(
            f"/families/{fam_id}/medications/{med_id}/members",
            headers={"Authorization": f"Bearer {token}"},
            json={"member_id": mem_id},
        )

        # 1. start_date > end_date -> 422
        bad_dates = client.post(
            f"/families/{fam_id}/prescriptions",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "member_id": mem_id,
                "title": "Đơn sai ngày",
                "start_date": "2026-11-20",
                "end_date": "2026-11-10",
            },
        )
        assert bad_dates.status_code == 422

        # Create valid prescription
        rx_id = client.post(
            f"/families/{fam_id}/prescriptions",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "member_id": mem_id,
                "title": "Đơn giảm đau",
                "start_date": "2026-11-01",
                "end_date": "2026-11-15",
            },
        ).json()["id"]

        # 2. Invalid dose_amount = -1 -> 422
        bad_dose = client.post(
            f"/families/{fam_id}/prescriptions/{rx_id}/items",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "family_medication_id": med_id,
                "dose_amount": -1,
                "dose_unit": "TABLET",
            },
        )
        assert bad_dose.status_code == 422

        # 3. Invalid frequency_per_day = -2 -> 422
        bad_freq = client.post(
            f"/families/{fam_id}/prescriptions/{rx_id}/items",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "family_medication_id": med_id,
                "dose_amount": 1,
                "dose_unit": "TABLET",
                "frequency_per_day": -2,
            },
        )
        assert bad_freq.status_code == 422

        # 4. Null frequency_per_day with frequency_text = "Khi cần" -> 201
        ok_prn = client.post(
            f"/families/{fam_id}/prescriptions/{rx_id}/items",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "family_medication_id": med_id,
                "dose_amount": 1,
                "dose_unit": "TABLET",
                "frequency_per_day": None,
                "frequency_text": "Khi cần",
                "route": "ORAL",
            },
        )
        assert ok_prn.status_code == 201
        assert ok_prn.json()["frequency_per_day"] is None
        assert ok_prn.json()["frequency_text"] == "Khi cần"
    finally:
        _cleanup([owner_id], family_ids, catalog_ids)
