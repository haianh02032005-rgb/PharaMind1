from collections import defaultdict
from typing import Any

from fastapi import WebSocket


class WebSocketManager:
    """Manages active WebSocket subscriptions scoped by (family_id, cabinet_id)."""

    def __init__(self) -> None:
        self._connections: dict[tuple[int, int], list[WebSocket]] = defaultdict(
            list
        )

    async def connect(
        self,
        family_id: int,
        cabinet_id: int,
        websocket: WebSocket,
    ) -> None:
        await websocket.accept()
        key = (family_id, cabinet_id)
        if websocket not in self._connections[key]:
            self._connections[key].append(websocket)

    def disconnect(
        self,
        family_id: int,
        cabinet_id: int,
        websocket: WebSocket,
    ) -> None:
        key = (family_id, cabinet_id)
        conns = self._connections.get(key)
        if not conns:
            return
        if websocket in conns:
            conns.remove(websocket)
        if not conns:
            self._connections.pop(key, None)

    async def broadcast(
        self,
        family_id: int,
        cabinet_id: int,
        message: dict[str, Any],
    ) -> None:
        key = (family_id, cabinet_id)
        conns = list(self._connections.get(key, []))
        stale: list[WebSocket] = []
        for ws in conns:
            try:
                await ws.send_json(message)
            except Exception:
                stale.append(ws)
        for ws in stale:
            self.disconnect(family_id, cabinet_id, ws)


websocket_manager = WebSocketManager()
