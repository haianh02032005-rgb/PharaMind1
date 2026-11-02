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


def test_prescription_update_complete_archive_and_edit_locks():
    """TASK 07 §29, §32–36, §60, §61: Update prescription, complete & archive locks against further edits."""
    owner_id, _, token = _create_user_and_token("rx_upd_owner")
    family_ids: list[int] = []
    catalog_ids: list[int] = []

    try:
        fam_id = client.post(
            "/families",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Family Rx Update"},
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
                "name": f"Med-{uuid4().hex[:6]}",
                "quantity": 30,
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

        rx = client.post(
            f"/families/{fam_id}/prescriptions",
            headers={"Authorization": f"Bearer {token}"},
            json={"member_id": mem_id, "title": "Đơn ban đầu"},
        ).json()
        rx_id = rx["id"]

        item_id = client.post(
            f"/families/{fam_id}/prescriptions/{rx_id}/items",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "family_medication_id": med_id,
                "dose_amount": 1,
                "dose_unit": "TABLET",
            },
        ).json()["id"]

        # Update prescription metadata -> 200
        upd_res = client.patch(
            f"/families/{fam_id}/prescriptions/{rx_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "title": "Đơn đã cập nhật",
                "doctor_name": "BS. Trần Văn C",
            },
        )
        assert upd_res.status_code == 200
        assert upd_res.json()["title"] == "Đơn đã cập nhật"

        # Changing member_id or family_id via PATCH is forbidden (422)
        assert (
            client.patch(
                f"/families/{fam_id}/prescriptions/{rx_id}",
                headers={"Authorization": f"Bearer {token}"},
                json={"member_id": 999},
            ).status_code
            == 422
        )

        # Archive prescription -> cannot update or add/update items (409)
        arch_res = client.post(
            f"/families/{fam_id}/prescriptions/{rx_id}/archive",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert arch_res.status_code == 200
        assert arch_res.json()["status"] == "ARCHIVED"

        assert (
            client.patch(
                f"/families/{fam_id}/prescriptions/{rx_id}",
                headers={"Authorization": f"Bearer {token}"},
                json={"title": "Sửa khi archived"},
            ).status_code
            == 409
        )
        assert (
            client.post(
                f"/families/{fam_id}/prescriptions/{rx_id}/items",
                headers={"Authorization": f"Bearer {token}"},
                json={"family_medication_id": med_id, "dose_amount": 1},
            ).status_code
            == 409
        )

        # Restore prescription -> back to ACTIVE
        rest_res = client.post(
            f"/families/{fam_id}/prescriptions/{rx_id}/restore",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert rest_res.status_code == 200
        assert rest_res.json()["status"] == "ACTIVE"

        # Complete prescription -> status = COMPLETED, further item edits rejected (409)
        comp_res = client.post(
            f"/families/{fam_id}/prescriptions/{rx_id}/complete",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert comp_res.status_code == 200
        assert comp_res.json()["status"] == "COMPLETED"

        assert (
            client.patch(
                f"/families/{fam_id}/prescriptions/{rx_id}/items/{item_id}",
                headers={"Authorization": f"Bearer {token}"},
                json={"dose_amount": 3},
            ).status_code
            == 409
        )
    finally:
        _cleanup([owner_id], family_ids, catalog_ids)
