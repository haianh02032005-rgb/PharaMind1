import re
from typing import Any

from backend.app.modules.imports.normalizers.date_normalizer import normalize_time_string

TIME_TOKEN_RE = re.compile(r"\b(\d{1,2}:\d{2})\b")


def parse_schedule_candidate(
    raw_item: dict[str, Any],
    normalized_med: dict[str, Any],
    prescription_meta: dict[str, Any],
) -> dict[str, Any]:
    """Parse schedule candidate without guessing HH:MM times (§13)."""
    raw_times = raw_item.get("schedule_times")
    explicit_times: list[str] = []

    if isinstance(raw_times, list):
        for t in raw_times:
            norm_t = normalize_time_string(str(t))
            if norm_t and norm_t not in explicit_times:
                explicit_times.append(norm_t)
    elif isinstance(raw_times, str) and raw_times.strip():
        for part in re.split(r"[,;|]+", raw_times):
            norm_t = normalize_time_string(part.strip())
            if norm_t and norm_t not in explicit_times:
                explicit_times.append(norm_t)

    # Also check instructions only for explicit HH:MM clock times (never guess from "sáng/tối")
    if not explicit_times:
        instructions_text = str(raw_item.get("instructions") or "")
        for match in TIME_TOKEN_RE.findall(instructions_text):
            norm_t = normalize_time_string(match)
            if norm_t and norm_t not in explicit_times:
                explicit_times.append(norm_t)

    explicit_times.sort()

    recurrence_type = str(raw_item.get("recurrence_type") or "DAILY").strip().upper()
    if recurrence_type not in {"DAILY", "INTERVAL_DAYS", "WEEKDAYS", "AS_NEEDED"}:
        recurrence_type = "DAILY"

    reminder_enabled = True
    if raw_item.get("reminder_enabled") is not None:
        val = str(raw_item.get("reminder_enabled")).strip().lower()
        reminder_enabled = val not in {"false", "0", "no", "off"}

    reminder_before = 15
    if raw_item.get("reminder_before_minutes") is not None and str(raw_item.get("reminder_before_minutes")).strip() != "":
        try:
            reminder_before = max(0, int(float(raw_item["reminder_before_minutes"])))
        except (ValueError, TypeError):
            reminder_before = 15

    grace_period = 30
    if raw_item.get("grace_period_minutes") is not None and str(raw_item.get("grace_period_minutes")).strip() != "":
        try:
            grace_period = max(1, int(float(raw_item["grace_period_minutes"])))
        except (ValueError, TypeError):
            grace_period = 30

    start_date = (
        normalized_med.get("start_date")
        or prescription_meta.get("start_date")
        or prescription_meta.get("issued_at")
    )
    end_date = normalized_med.get("end_date") or prescription_meta.get("end_date")

    freq = normalized_med.get("frequency_per_day")
    create_schedule = bool(explicit_times or (freq and freq > 0))

    return {
        "create_schedule": create_schedule,
        "recurrence_type": recurrence_type,
        "schedule_times": explicit_times,
        "start_date": start_date,
        "end_date": end_date,
        "reminder_enabled": reminder_enabled,
        "reminder_before_minutes": reminder_before,
        "grace_period_minutes": grace_period,
    }

