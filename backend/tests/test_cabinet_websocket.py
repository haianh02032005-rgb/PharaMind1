from uuid import uuid4

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import delete
from starlette.websockets import WebSocketDisconnect

from backend.app.db.session import SessionLocal
from backend.app.main import app
from backend.app.models.cabinet import Cabinet
from backend.app.models.family import Family
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


def _cleanup(user_ids: list[int], family_ids: list[int]) -> None:
    with SessionLocal() as session:
        if family_ids:
            session.execute(
                delete(Cabinet).where(Cabinet.family_id.in_(family_ids))
            )
            session.execute(delete(Family).where(Family.id.in_(family_ids)))
        if user_ids:
            session.execute(delete(User).where(User.id.in_(user_ids)))
        session.commit()


def test_cabinet_websocket_authorization_and_realtime_events():
    """TASK 09 §43–49, §90, §91: Reject unauthorized WebSocket connections and push realtime events to subscribed family members."""
    owner_id, _, owner_token = _create_user_and_token("cab_ws_owner")
    outsider_id, _, outsider_token = _create_user_and_token("cab_ws_outsider")
    family_ids: list[int] = []

    try:
        fam_id = client.post(
            "/families",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={"name": "WS Family"},
        ).json()["id"]
        family_ids.append(fam_id)

        cab_id = client.post(
            f"/families/{fam_id}/cabinets",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={
                "name": "Tủ Realtime",
                "device_code": f"PM-CAB-{uuid4().hex[:8].upper()}",
            },
        ).json()["id"]

        # 1. Outsider cannot subscribe -> WebSocketDisconnect (1008) (§90)
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect(
                f"/ws/families/{fam_id}/cabinets/{cab_id}?token={outsider_token}"
            ) as ws_unauth:
                ws_unauth.receive_json()

        # 2. Authorized member subscribes and receives CABINET_ONLINE, COMPARTMENT_OPEN, COMPARTMENT_CLOSE (§46–48, §91)
        with client.websocket_connect(
            f"/ws/families/{fam_id}/cabinets/{cab_id}?token={owner_token}"
        ) as ws:
            client.post(
                f"/families/{fam_id}/cabinets/{cab_id}/simulator/online",
                headers={"Authorization": f"Bearer {owner_token}"},
            )
            msg_online = ws.receive_json()
            assert msg_online["type"] == "CABINET_ONLINE"
            assert msg_online["cabinet_id"] == cab_id

            client.post(
                f"/families/{fam_id}/cabinets/{cab_id}/compartments/6/open",
                headers={"Authorization": f"Bearer {owner_token}"},
            )
            msg_open = ws.receive_json()
            assert msg_open["type"] == "COMPARTMENT_OPEN"
            assert msg_open["cabinet_id"] == cab_id
            assert msg_open["compartment"]["position"] == 6
            assert msg_open["compartment"]["object_id"] == "drawer_06"

            client.post(
                f"/families/{fam_id}/cabinets/{cab_id}/compartments/6/close",
                headers={"Authorization": f"Bearer {owner_token}"},
            )
            msg_close = ws.receive_json()
            assert msg_close["type"] == "COMPARTMENT_CLOSE"
            assert msg_close["compartment"]["position"] == 6
    finally:
        _cleanup([owner_id, outsider_id], family_ids)

