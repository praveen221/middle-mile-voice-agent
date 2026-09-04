"""Sample availability table. Swap for your own calendar."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from src.tools.rate_card import normalize_place

# Remaining slots by location + ISO date. Clock is frozen so the sample stays deterministic.
AVAILABILITY: dict[tuple[str, str], dict[str, Any]] = {
    ("ANDHERI", "2026-08-14"): {
        "slots": 2,
        "next_available": "2026-08-14",
        "window": "16:00-18:00",
        "reserved_for": "BK-1001",
        "reserved_window": "16:00-18:00",
        "gate_out_latest": "15:30",
        "note": "Room 2 is held until 15:30. After that it is released. Next opening is 2026-08-15.",
    },
    ("ANDHERI", "2026-08-15"): {"slots": 1, "next_available": "2026-08-15", "window": "10:00-14:00"},
    ("BANDRA", "2026-08-14"): {"slots": 0, "next_available": "2026-08-15", "window": None},
    ("BANDRA", "2026-08-15"): {"slots": 3, "next_available": "2026-08-15", "window": "09:00-18:00"},
    ("POWAI", "2026-08-14"): {
        "slots": 0,
        "next_available": "2026-08-15",
        "window": None,
        "note": "BK-1002 hold expired at 15:30. Next opening tomorrow.",
    },
    ("WORLI", "2026-08-14"): {"slots": 1, "next_available": "2026-08-14", "window": "16:00-20:00"},
}


def _parse_date(value: str) -> str:
    text = value.strip()
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    lowered = text.lower()
    today = date(2026, 8, 13)
    if lowered in {"today", "aaj"}:
        return today.isoformat()
    if lowered in {"tomorrow", "kal"}:
        return date(2026, 8, 14).isoformat()
    return text


def check_availability(location: str, date_str: str) -> dict[str, Any]:
    """Check remaining slots at a location for a date.

    Args:
        location: Place name.
        date_str: Date as YYYY-MM-DD, or 'today' / 'tomorrow'.
    """
    loc = normalize_place(location)
    day = _parse_date(date_str)
    row = AVAILABILITY.get((loc, day))
    if row is None:
        return {
            "found": False,
            "location": loc,
            "date": day,
            "slots": 0,
            "message": "No availability record. Treat as unknown and confirm with the venue.",
        }
    available = int(row["slots"]) > 0
    payload = {
        "found": True,
        "location": loc,
        "date": day,
        "slots": row["slots"],
        "available": available,
        "window": row["window"],
        "next_available": row["next_available"],
    }
    for key in ("reserved_for", "reserved_window", "gate_out_latest", "note"):
        if key in row:
            payload[key] = row[key]
    return payload


check_capacity = check_availability
