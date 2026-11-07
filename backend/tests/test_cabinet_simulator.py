from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import delete

from backend.app.db.session import SessionLocal
from backend.app.integrations.hardware.simulator import hardware_simulator
from backend.app.main import app
from backend.app.models.cabinet import Cabinet
from backend.app.models.family import Family
from backend.app.models.medication_catalog import MedicationCatalog
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


def test_simulator_online_offline_open_close_inventory_unchanged_and_state_sync():
    """TASK 09 §34–40, §54, §58–60, §84–89, §92: Online/offline, offline open 409, open/close compartment, inventory unchanged, state sync."""
    user_id, _, token = _create_user_and_token("cab_sim")
    family_ids: list[int] = []
    catalog_ids: list[int] = []

    try:
        fam_id = client.post(
            "/families",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Simulator Family"},
        ).json()["id"]
        family_ids.append(fam_id)

        cab = client.post(
            f"/families/{fam_id}/cabinets",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "Tủ mô phỏng",
                "device_code": f"PM-CAB-{uuid4().hex[:8].upper()}",
            },
        ).json()
        cab_id = cab["id"]

        med = client.post(
            f"/families/{fam_id}/medications",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": f"Amlodipine_{uuid4().hex[:6]}",
                "quantity": 20,
                "unit": "TABLET",
            },
        ).json()
        catalog_ids.append(med["catalog"]["id"])

        client.put(
            f"/families/{fam_id}/cabinets/{cab_id}/compartments/6/medication",
            headers={"Authorization": f"Bearer {token}"},
            json={"family_medication_id": med["id"]},
        )

        # 1. Open compartment while OFFLINE -> 409 (§38, §85)
        offline_open = client.post(
            f"/families/{fam_id}/cabinets/{cab_id}/compartments/6/open",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert offline_open.status_code == 409

        # 2. Set simulator ONLINE -> status ONLINE (§34, §84)
        online_res = client.post(
            f"/families/{fam_id}/cabinets/{cab_id}/simulator/online",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert online_res.status_code == 200
        assert online_res.json()["status"] == "ONLINE"
        assert online_res.json()["last_seen_at"] is not None

        # 3. Open compartment 8 -> is_open=true, status=OPEN (§36, §86)
        open_res = client.post(
            f"/families/{fam_id}/cabinets/{cab_id}/compartments/6/open",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert open_res.status_code == 200
        assert open_res.json()["is_open"] is True
        assert open_res.json()["status"] == "OPEN"

        # 4. Close compartment 8 -> is_open=false, status=AVAILABLE (§37, §87)
        close_res = client.post(
            f"/families/{fam_id}/cabinets/{cab_id}/compartments/6/close",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert close_res.status_code == 200
        assert close_res.json()["is_open"] is False
        assert close_res.json()["status"] == "AVAILABLE"

        # 5. Verify inventory quantity is still 20 (§60, §88)
        med_after = client.get(
            f"/families/{fam_id}/medications/{med['id']}",
            headers={"Authorization": f"Bearer {token}"},
        ).json()
        assert med_after["quantity"] == 20.0

        # 6. State Sync: mutate simulator raw state (position 8 open) and call /simulator/sync (§54, §92)
        hardware_simulator.set_raw_compartment_state(
            cab_id,
            6,
            is_open=True,
            cabinet_status="ONLINE",
        )
        sync_res = client.post(
            f"/families/{fam_id}/cabinets/{cab_id}/simulator/sync",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert sync_res.status_code == 200
        state_data = sync_res.json()
        comp_8_state = next(
            c for c in state_data["compartments"] if c["position"] == 6
        )
        assert comp_8_state["is_open"] is True
        assert comp_8_state["status"] == "OPEN"
    finally:
        _cleanup([user_id], family_ids, catalog_ids)

