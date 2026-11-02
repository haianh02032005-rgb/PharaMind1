from datetime import datetime, timezone
from typing import Any


def build_cabinet_ws_event(
    *,
    event_type: str,
    cabinet_id: int,
    compartment_id: int | None = None,
    compartment_position: int | None = None,
    occurred_at: datetime | None = None,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ts = occurred_at or datetime.now(timezone.utc)
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    iso_ts = ts.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

    message: dict[str, Any] = {
        "type": event_type,
        "cabinet_id": cabinet_id,
        "timestamp": iso_ts,
    }
    if compartment_id is not None or compartment_position is not None:
        message["compartment"] = {
            "id": compartment_id,
            "position": compartment_position,
            "object_id": (
                f"drawer_{compartment_position:02d}"
                if compartment_position is not None
                else None
            ),
        }
    if payload:
        message["payload"] = payload
    return message
