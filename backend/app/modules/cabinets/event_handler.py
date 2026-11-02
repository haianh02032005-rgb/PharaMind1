from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from backend.app.models.cabinet import Cabinet
from backend.app.models.compartment import Compartment
from backend.app.modules.cabinets.enums import (
    CabinetEventType,
    CabinetStatus,
)
from backend.app.modules.cabinets.repository import CabinetRepository
from backend.app.realtime.events import build_cabinet_ws_event
from backend.app.realtime.websocket_manager import (
    WebSocketManager,
    websocket_manager,
)


class CabinetEventHandler:
    """Reconciles hardware/simulator events into PostgreSQL and publishes WebSocket notifications."""

    def __init__(
        self,
        repository: CabinetRepository | None = None,
        ws_manager: WebSocketManager | None = None,
    ) -> None:
        self.repository = repository or CabinetRepository()
        self.ws_manager = ws_manager or websocket_manager

    async def handle_cabinet_online(
        self,
        db: Session,
        cabinet: Cabinet,
        *,
        source: str = "SIMULATOR",
    ) -> Cabinet:
        now = datetime.now(timezone.utc)
        updated = self.repository.update_cabinet_status(
            db,
            cabinet,
            status=CabinetStatus.ONLINE.value,
            last_seen_at=now,
        )
        evt = self.repository.create_event(
            db,
            family_id=cabinet.family_id,
            cabinet_id=cabinet.id,
            event_type=CabinetEventType.CABINET_ONLINE.value,
            source=source,
            payload={"status": CabinetStatus.ONLINE.value},
            occurred_at=now,
        )
        db.commit()
        db.refresh(updated)

        ws_msg = build_cabinet_ws_event(
            event_type=CabinetEventType.CABINET_ONLINE.value,
            cabinet_id=cabinet.id,
            occurred_at=evt.occurred_at,
        )
        await self.ws_manager.broadcast(
            cabinet.family_id,
            cabinet.id,
            ws_msg,
        )
        return updated

    async def handle_cabinet_offline(
        self,
        db: Session,
        cabinet: Cabinet,
        *,
        source: str = "SIMULATOR",
    ) -> Cabinet:
        now = datetime.now(timezone.utc)
        updated = self.repository.update_cabinet_status(
            db,
            cabinet,
            status=CabinetStatus.OFFLINE.value,
            last_seen_at=now,
        )
        evt = self.repository.create_event(
            db,
            family_id=cabinet.family_id,
            cabinet_id=cabinet.id,
            event_type=CabinetEventType.CABINET_OFFLINE.value,
            source=source,
            payload={"status": CabinetStatus.OFFLINE.value},
            occurred_at=now,
        )
        db.commit()
        db.refresh(updated)

        ws_msg = build_cabinet_ws_event(
            event_type=CabinetEventType.CABINET_OFFLINE.value,
            cabinet_id=cabinet.id,
            occurred_at=evt.occurred_at,
        )
        await self.ws_manager.broadcast(
            cabinet.family_id,
            cabinet.id,
            ws_msg,
        )
        return updated

    async def handle_compartment_open(
        self,
        db: Session,
        cabinet: Cabinet,
        compartment: Compartment,
        *,
        source: str = "SIMULATOR",
    ) -> Compartment:
        now = datetime.now(timezone.utc)
        cabinet.last_seen_at = now
        db.add(cabinet)

        updated_comp = self.repository.update_compartment_state(
            db,
            compartment,
            is_open=True,
        )
        evt = self.repository.create_event(
            db,
            family_id=cabinet.family_id,
            cabinet_id=cabinet.id,
            compartment_id=compartment.id,
            event_type=CabinetEventType.COMPARTMENT_OPEN.value,
            source=source,
            payload={
                "position": compartment.position,
                "is_open": True,
            },
            occurred_at=now,
        )
        db.commit()
        db.refresh(updated_comp)

        ws_msg = build_cabinet_ws_event(
            event_type=CabinetEventType.COMPARTMENT_OPEN.value,
            cabinet_id=cabinet.id,
            compartment_id=updated_comp.id,
            compartment_position=updated_comp.position,
            occurred_at=evt.occurred_at,
        )
        await self.ws_manager.broadcast(
            cabinet.family_id,
            cabinet.id,
            ws_msg,
        )
        return updated_comp

    async def handle_compartment_close(
        self,
        db: Session,
        cabinet: Cabinet,
        compartment: Compartment,
        *,
        source: str = "SIMULATOR",
    ) -> Compartment:
        now = datetime.now(timezone.utc)
        cabinet.last_seen_at = now
        db.add(cabinet)

        updated_comp = self.repository.update_compartment_state(
            db,
            compartment,
            is_open=False,
        )
        evt = self.repository.create_event(
            db,
            family_id=cabinet.family_id,
            cabinet_id=cabinet.id,
            compartment_id=compartment.id,
            event_type=CabinetEventType.COMPARTMENT_CLOSE.value,
            source=source,
            payload={
                "position": compartment.position,
                "is_open": False,
            },
            occurred_at=now,
        )
        db.commit()
        db.refresh(updated_comp)

        ws_msg = build_cabinet_ws_event(
            event_type=CabinetEventType.COMPARTMENT_CLOSE.value,
            cabinet_id=cabinet.id,
            compartment_id=updated_comp.id,
            compartment_position=updated_comp.position,
            occurred_at=evt.occurred_at,
        )
        await self.ws_manager.broadcast(
            cabinet.family_id,
            cabinet.id,
            ws_msg,
        )
        return updated_comp

    async def handle_device_error(
        self,
        db: Session,
        cabinet: Cabinet,
        *,
        payload: dict[str, Any] | None = None,
        source: str = "SIMULATOR",
    ) -> Cabinet:
        now = datetime.now(timezone.utc)
        updated = self.repository.update_cabinet_status(
            db,
            cabinet,
            status=CabinetStatus.ERROR.value,
            last_seen_at=now,
        )
        evt = self.repository.create_event(
            db,
            family_id=cabinet.family_id,
            cabinet_id=cabinet.id,
            event_type=CabinetEventType.DEVICE_ERROR.value,
            source=source,
            payload=payload or {"status": CabinetStatus.ERROR.value},
            occurred_at=now,
        )
        db.commit()
        db.refresh(updated)

        ws_msg = build_cabinet_ws_event(
            event_type=CabinetEventType.DEVICE_ERROR.value,
            cabinet_id=cabinet.id,
            occurred_at=evt.occurred_at,
            payload=payload,
        )
        await self.ws_manager.broadcast(
            cabinet.family_id,
            cabinet.id,
            ws_msg,
        )
        return updated

    async def handle_state_sync(
        self,
        db: Session,
        cabinet: Cabinet,
        simulator_state: dict[str, Any],
        *,
        source: str = "SIMULATOR",
    ) -> Cabinet:
        now = datetime.now(timezone.utc)
        sim_status = simulator_state.get("status")
        if sim_status in {
            CabinetStatus.ONLINE.value,
            CabinetStatus.OFFLINE.value,
            CabinetStatus.ERROR.value,
        }:
            cabinet.status = sim_status
        cabinet.last_seen_at = now
        db.add(cabinet)

        comp_by_pos = {c.position: c for c in cabinet.compartments}
        sim_comps = simulator_state.get("compartments") or []
        for sim_c in sim_comps:
            pos = sim_c.get("position")
            is_open = bool(sim_c.get("is_open", False))
            if pos in comp_by_pos:
                self.repository.update_compartment_state(
                    db,
                    comp_by_pos[pos],
                    is_open=is_open,
                )

        evt = self.repository.create_event(
            db,
            family_id=cabinet.family_id,
            cabinet_id=cabinet.id,
            event_type=CabinetEventType.STATE_SYNC.value,
            source=source,
            payload=simulator_state,
            occurred_at=now,
        )
        db.commit()
        db.refresh(cabinet)

        ws_msg = build_cabinet_ws_event(
            event_type=CabinetEventType.STATE_SYNC.value,
            cabinet_id=cabinet.id,
            occurred_at=evt.occurred_at,
            payload=simulator_state,
        )
        await self.ws_manager.broadcast(
            cabinet.family_id,
            cabinet.id,
            ws_msg,
        )
        return cabinet

