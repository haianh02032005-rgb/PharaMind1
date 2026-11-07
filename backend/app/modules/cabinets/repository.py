from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.cabinet import Cabinet
from backend.app.models.cabinet_event import CabinetEvent
from backend.app.models.compartment import Compartment
from backend.app.modules.cabinets.enums import CabinetStatus, CompartmentStatus


class CabinetRepository:
    # ------------------------------------------------------------------
    # Cabinet Persistence
    # ------------------------------------------------------------------

    def create_cabinet(
        self,
        db: Session,
        cabinet: Cabinet,
    ) -> Cabinet:
        db.add(cabinet)
        db.flush()
        return cabinet

    def get_cabinet(
        self,
        db: Session,
        *,
        family_id: int,
        cabinet_id: int,
    ) -> Cabinet | None:
        stmt = select(Cabinet).where(
            Cabinet.id == cabinet_id,
            Cabinet.family_id == family_id,
        )
        return db.scalar(stmt)

    def get_cabinet_by_device_code(
        self,
        db: Session,
        *,
        device_code: str,
    ) -> Cabinet | None:
        stmt = select(Cabinet).where(Cabinet.device_code == device_code)
        return db.scalar(stmt)

    def get_active_cabinet_for_family(
        self,
        db: Session,
        *,
        family_id: int,
    ) -> Cabinet | None:
        stmt = select(Cabinet).where(
            Cabinet.family_id == family_id,
            Cabinet.status != CabinetStatus.ARCHIVED.value,
        )
        return db.scalar(stmt)

    def list_cabinets(
        self,
        db: Session,
        *,
        family_id: int,
        include_archived: bool = False,
    ) -> list[Cabinet]:
        stmt = select(Cabinet).where(Cabinet.family_id == family_id)
        if not include_archived:
            stmt = stmt.where(Cabinet.status != CabinetStatus.ARCHIVED.value)
        stmt = stmt.order_by(Cabinet.id.asc())
        return list(db.scalars(stmt).unique().all())

    def update_cabinet_status(
        self,
        db: Session,
        cabinet: Cabinet,
        *,
        status: str,
        last_seen_at: datetime | None = None,
    ) -> Cabinet:
        cabinet.status = status
        if last_seen_at is not None:
            cabinet.last_seen_at = last_seen_at
        db.add(cabinet)
        db.flush()
        return cabinet

    # ------------------------------------------------------------------
    # Compartment Persistence
    # ------------------------------------------------------------------

    def create_compartments(
        self,
        db: Session,
        *,
        cabinet_id: int,
        count: int = 6,
    ) -> list[Compartment]:
        created: list[Compartment] = []
        for pos in range(1, count + 1):
            comp = Compartment(
                cabinet_id=cabinet_id,
                position=pos,
                label=f"Ngăn {pos:02d}",
                status=CompartmentStatus.EMPTY.value,
                is_open=False,
            )
            db.add(comp)
            created.append(comp)
        db.flush()
        return created

    def get_compartment(
        self,
        db: Session,
        *,
        family_id: int,
        cabinet_id: int,
        position: int,
    ) -> Compartment | None:
        stmt = (
            select(Compartment)
            .join(Cabinet, Cabinet.id == Compartment.cabinet_id)
            .where(
                Cabinet.family_id == family_id,
                Compartment.cabinet_id == cabinet_id,
                Compartment.position == position,
            )
        )
        return db.scalar(stmt)

    def get_compartment_by_medication(
        self,
        db: Session,
        *,
        family_medication_id: int,
    ) -> Compartment | None:
        stmt = select(Compartment).where(
            Compartment.family_medication_id == family_medication_id
        )
        return db.scalar(stmt)

    def list_compartments(
        self,
        db: Session,
        *,
        cabinet_id: int,
    ) -> list[Compartment]:
        stmt = (
            select(Compartment)
            .where(Compartment.cabinet_id == cabinet_id)
            .order_by(Compartment.position.asc())
        )
        return list(db.scalars(stmt).unique().all())

    def assign_medication(
        self,
        db: Session,
        compartment: Compartment,
        *,
        family_medication_id: int,
    ) -> Compartment:
        compartment.family_medication_id = family_medication_id
        if not compartment.is_open:
            compartment.status = CompartmentStatus.AVAILABLE.value
        db.add(compartment)
        db.flush()
        return compartment

    def unassign_medication(
        self,
        db: Session,
        compartment: Compartment,
    ) -> Compartment:
        compartment.family_medication_id = None
        if not compartment.is_open:
            compartment.status = CompartmentStatus.EMPTY.value
        db.add(compartment)
        db.flush()
        return compartment

    def update_compartment_state(
        self,
        db: Session,
        compartment: Compartment,
        *,
        is_open: bool,
    ) -> Compartment:
        compartment.is_open = is_open
        if is_open:
            compartment.status = CompartmentStatus.OPEN.value
        else:
            compartment.status = (
                CompartmentStatus.AVAILABLE.value
                if compartment.family_medication_id is not None
                else CompartmentStatus.EMPTY.value
            )
        db.add(compartment)
        db.flush()
        return compartment

    # ------------------------------------------------------------------
    # CabinetEvent Persistence
    # ------------------------------------------------------------------

    def create_event(
        self,
        db: Session,
        *,
        family_id: int,
        cabinet_id: int,
        compartment_id: int | None = None,
        event_type: str,
        source: str = "SIMULATOR",
        payload: dict[str, Any] | None = None,
        occurred_at: datetime | None = None,
    ) -> CabinetEvent:
        evt = CabinetEvent(
            family_id=family_id,
            cabinet_id=cabinet_id,
            compartment_id=compartment_id,
            event_type=event_type,
            source=source,
            payload=payload,
        )
        if occurred_at is not None:
            evt.occurred_at = occurred_at
        db.add(evt)
        db.flush()
        return evt

    def list_events(
        self,
        db: Session,
        *,
        family_id: int,
        cabinet_id: int,
        event_type: str | None = None,
        from_time: datetime | None = None,
        to_time: datetime | None = None,
        limit: int = 100,
    ) -> list[CabinetEvent]:
        stmt = select(CabinetEvent).where(
            CabinetEvent.family_id == family_id,
            CabinetEvent.cabinet_id == cabinet_id,
        )
        if event_type is not None:
            stmt = stmt.where(CabinetEvent.event_type == event_type)
        if from_time is not None:
            stmt = stmt.where(CabinetEvent.occurred_at >= from_time)
        if to_time is not None:
            stmt = stmt.where(CabinetEvent.occurred_at <= to_time)

        stmt = stmt.order_by(
            CabinetEvent.occurred_at.desc(),
            CabinetEvent.id.desc(),
        ).limit(limit)
        return list(db.scalars(stmt).unique().all())
