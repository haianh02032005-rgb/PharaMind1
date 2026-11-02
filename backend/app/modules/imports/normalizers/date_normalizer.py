import re
from datetime import date, datetime


def normalize_date(value: str | date | datetime | None) -> str | None:
    """Normalize a date string or date object into ISO YYYY-MM-DD format."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()

    raw = str(value).strip()
    if not raw:
        return None

    # Standard YYYY-MM-DD
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d", "%d.%m.%Y"):
        try:
            return datetime.strptime(raw, fmt).date().isoformat()
        except ValueError:
            continue

    # Vietnamese text pattern: Ngày 01 tháng 11 năm 2026
    m = re.search(
        r"(?:ngay|ngày)?\s*(\d{1,2})\s*(?:thang|tháng|/|-)\s*(\d{1,2})\s*(?:nam|năm|/|-)\s*(\d{4})",
        raw,
        re.IGNORECASE,
    )
    if m:
        day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            return date(year, month, day).isoformat()
        except ValueError:
            return None

    return None


def parse_iso_date(value: str | date | None) -> date | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    iso_str = normalize_date(value)
    if not iso_str:
        return None
    try:
        return date.fromisoformat(iso_str)
    except ValueError:
        return None


def normalize_time_string(value: str | None) -> str | None:
    """Normalize HH:MM time strings."""
    if not value:
        return None
    raw = str(value).strip()
    m = re.match(r"^(\d{1,2}):(\d{2})(?::\d{2})?$", raw)
    if not m:
        return None
    hour, minute = int(m.group(1)), int(m.group(2))
    if 0 <= hour <= 23 and 0 <= minute <= 59:
        return f"{hour:02d}:{minute:02d}"
    return None

