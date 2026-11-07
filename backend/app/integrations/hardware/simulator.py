from typing import Any

from backend.app.integrations.hardware.base import HardwareAdapter


class HardwareSimulator(HardwareAdapter):
    """In-process Hardware Simulator managing simulated cabinet and drawer states."""

    def __init__(self) -> None:
        self._cabinets: dict[int, dict[str, Any]] = {}

    def _ensure_cabinet(
        self,
        cabinet_id: int,
        status: str = "OFFLINE",
        positions: list[int] | None = None,
    ) -> dict[str, Any]:
        if cabinet_id not in self._cabinets:
            pos_list = positions or list(range(1, 7))
            self._cabinets[cabinet_id] = {
                "cabinet_id": cabinet_id,
                "status": status,
                "compartments": {
                    pos: {"position": pos, "is_open": False}
                    for pos in sorted(pos_list)
                },
            }
        return self._cabinets[cabinet_id]

    def _serialize(self, cabinet_id: int) -> dict[str, Any]:
        state = self._ensure_cabinet(cabinet_id)
        return {
            "cabinet_id": state["cabinet_id"],
            "status": state["status"],
            "compartments": [
                {
                    "position": pos,
                    "is_open": bool(comp["is_open"]),
                }
                for pos, comp in sorted(state["compartments"].items())
            ],
        }

    async def initialize_cabinet(
        self,
        cabinet_id: int,
        status: str = "OFFLINE",
        positions: list[int] | None = None,
    ) -> dict[str, Any]:
        pos_list = positions or list(range(1, 7))
        self._cabinets[cabinet_id] = {
            "cabinet_id": cabinet_id,
            "status": status,
            "compartments": {
                pos: {"position": pos, "is_open": False}
                for pos in sorted(pos_list)
            },
        }
        return self._serialize(cabinet_id)

    async def set_online(self, cabinet_id: int) -> dict[str, Any]:
        state = self._ensure_cabinet(cabinet_id)
        state["status"] = "ONLINE"
        return {
            "event": "CABINET_ONLINE",
            "cabinet_id": cabinet_id,
            "status": "ONLINE",
        }

    async def set_offline(self, cabinet_id: int) -> dict[str, Any]:
        state = self._ensure_cabinet(cabinet_id)
        state["status"] = "OFFLINE"
        return {
            "event": "CABINET_OFFLINE",
            "cabinet_id": cabinet_id,
            "status": "OFFLINE",
        }

    async def open_compartment(
        self,
        cabinet_id: int,
        position: int,
    ) -> dict[str, Any]:
        state = self._ensure_cabinet(cabinet_id)
        comp = state["compartments"].setdefault(
            position, {"position": position, "is_open": False}
        )
        comp["is_open"] = True
        return {
            "event": "COMPARTMENT_OPEN",
            "cabinet_id": cabinet_id,
            "position": position,
            "is_open": True,
        }

    async def close_compartment(
        self,
        cabinet_id: int,
        position: int,
    ) -> dict[str, Any]:
        state = self._ensure_cabinet(cabinet_id)
        comp = state["compartments"].setdefault(
            position, {"position": position, "is_open": False}
        )
        comp["is_open"] = False
        return {
            "event": "COMPARTMENT_CLOSE",
            "cabinet_id": cabinet_id,
            "position": position,
            "is_open": False,
        }

    async def get_state(self, cabinet_id: int) -> dict[str, Any]:
        return self._serialize(cabinet_id)

    def set_raw_compartment_state(
        self,
        cabinet_id: int,
        position: int,
        *,
        is_open: bool,
        cabinet_status: str | None = None,
    ) -> dict[str, Any]:
        """Helper for tests or simulator scenarios to mutate raw simulator state before sync."""
        state = self._ensure_cabinet(cabinet_id)
        if cabinet_status is not None:
            state["status"] = cabinet_status
        comp = state["compartments"].setdefault(
            position, {"position": position, "is_open": False}
        )
        comp["is_open"] = is_open
        return self._serialize(cabinet_id)

    def reset(self, cabinet_id: int | None = None) -> None:
        if cabinet_id is None:
            self._cabinets.clear()
        else:
            self._cabinets.pop(cabinet_id, None)


hardware_simulator = HardwareSimulator()

