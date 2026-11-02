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


def test_prescription_item_crud_link_requirement_and_duplicate_protection():
    """TASK 07 §17–22, §30, §31, §41, §42, §53–55: Item CRUD, requires member link, blocks duplicates & cross-family."""
    user_a_id, _, token_a = _create_user_and_token("rx_item_a")
    user_b_id, _, token_b = _create_user_and_token("rx_item_b")
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

        member_a1 = client.post(
            f"/families/{fam_a}/members",
            headers={"Authorization": f"Bearer {token_a}"},
            json={"full_name": "Bà Lan"},
        ).json()["id"]

        med_a1 = client.post(
            f"/families/{fam_a}/medications",
            headers={"Authorization": f"Bearer {token_a}"},
            json={
                "name": f"Amlodipine-{uuid4().hex[:6]}",
                "strength": "5 mg",
                "quantity": 30,
                "unit": "TABLET",
            },
        ).json()
        med_a1_id = med_a1["id"]
        catalog_ids.append(med_a1["catalog"]["id"])

        med_b1 = client.post(
            f"/families/{fam_b}/medications",
            headers={"Authorization": f"Bearer {token_b}"},
            json={
                "name": f"OtherMed-{uuid4().hex[:6]}",
                "quantity": 10,
                "unit": "TABLET",
            },
        ).json()
        med_b1_id = med_b1["id"]
        catalog_ids.append(med_b1["catalog"]["id"])

        rx_id = client.post(
            f"/families/{fam_a}/prescriptions",
            headers={"Authorization": f"Bearer {token_a}"},
            json={"member_id": member_a1, "title": "Đơn huyết áp"},
        ).json()["id"]

        # 1. Medication not linked to member_a1 yet -> rejected with 409
        unlinked_res = client.post(
            f"/families/{fam_a}/prescriptions/{rx_id}/items",
            headers={"Authorization": f"Bearer {token_a}"},
            json={
                "family_medication_id": med_a1_id,
                "dose_amount": 1,
                "dose_unit": "TABLET",
                "frequency_per_day": 1,
                "frequency_text": "1 lần/ngày",
                "route": "ORAL",
                "instructions": "Uống sau ăn sáng",
            },
        )
        assert unlinked_res.status_code == 409

        # 2. Cross-family medication (med_b1 from Family B) -> rejected with 404
        cross_med_res = client.post(
            f"/families/{fam_a}/prescriptions/{rx_id}/items",
            headers={"Authorization": f"Bearer {token_a}"},
            json={"family_medication_id": med_b1_id, "dose_amount": 1},
        )
        assert cross_med_res.status_code == 404

        # 3. Link med_a1 to member_a1, then add item -> 201
        client.post(
            f"/families/{fam_a}/medications/{med_a1_id}/members",
            headers={"Authorization": f"Bearer {token_a}"},
            json={"member_id": member_a1},
        )

        add_res = client.post(
            f"/families/{fam_a}/prescriptions/{rx_id}/items",
            headers={"Authorization": f"Bearer {token_a}"},
            json={
                "family_medication_id": med_a1_id,
                "dose_amount": 1,
                "dose_unit": "TABLET",
                "frequency_per_day": 1,
                "frequency_text": "1 lần/ngày",
                "route": "ORAL",
                "instructions": "Uống sau ăn sáng",
            },
        )
        assert add_res.status_code == 201
        item = add_res.json()
        item_id = item["id"]
        assert item["medication"]["id"] == med_a1_id
        assert item["medication"]["strength"] == "5 mg"
        assert item["dose_amount"] == 1
        assert item["dose_unit"] == "TABLET"
        assert item["route"] == "ORAL"

        # 4. Duplicate medication in same prescription -> 409
        dup_res = client.post(
            f"/families/{fam_a}/prescriptions/{rx_id}/items",
            headers={"Authorization": f"Bearer {token_a}"},
            json={
                "family_medication_id": med_a1_id,
                "dose_amount": 2,
                "dose_unit": "TABLET",
            },
        )
        assert dup_res.status_code == 409

        # 5. Update item (dose_amount, frequency_text, instructions) -> 200
        upd_item = client.patch(
            f"/families/{fam_a}/prescriptions/{rx_id}/items/{item_id}",
            headers={"Authorization": f"Bearer {token_a}"},
            json={
                "dose_amount": 2,
                "frequency_per_day": 2,
                "frequency_text": "2 lần/ngày",
                "instructions": "Sáng và tối",
            },
        )
        assert upd_item.status_code == 200
        assert upd_item.json()["dose_amount"] == 2
        assert upd_item.json()["frequency_per_day"] == 2

        # 6. Delete item -> 204
        del_res = client.delete(
            f"/families/{fam_a}/prescriptions/{rx_id}/items/{item_id}",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert del_res.status_code == 204

        rx_detail = client.get(
            f"/families/{fam_a}/prescriptions/{rx_id}",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert rx_detail.json()["items"] == []
    finally:
        _cleanup([user_a_id, user_b_id], family_ids, catalog_ids)
