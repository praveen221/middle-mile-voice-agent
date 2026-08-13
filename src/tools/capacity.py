"""Warehouse / hub capacity. Swap the table for WMS later."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from src.tools.rate_card import normalize_city

# Remaining outbound slots by location + ISO date.
CAPACITY: dict[tuple[str, str], dict[str, Any]] = {
    ("BLR", "2026-08-14"): {
        "slots": 3,
        "next_available": "2026-08-14",
        "window": "10:00-16:00",
        "reserved_for": "MM-1001",
        "reserved_window": "10:30-11:30",
        "gate_out_latest": "12:00",
        "note": "Dock 2 is held until 12:00. After that it is released. Next DC receiving for this customer is 2026-08-16.",
    },
    ("BLR", "2026-08-15"): {"slots": 1, "next_available": "2026-08-15", "window": "08:00-12:00"},
    ("HYD", "2026-08-14"): {"slots": 0, "next_available": "2026-08-15", "window": None},
    ("HYD", "2026-08-15"): {"slots": 4, "next_available": "2026-08-15", "window": "09:00-18:00"},
    ("CHN", "2026-08-14"): {"slots": 2, "next_available": "2026-08-14", "window": "11:00-17:00"},
    ("DEL", "2026-08-14"): {"slots": 5, "next_available": "2026-08-14", "window": "00:00-23:59"},
    ("MUM", "2026-08-14"): {"slots": 0, "next_available": "2026-08-16", "window": None},
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


def check_capacity(location: str, date_str: str) -> dict[str, Any]:
    """Check remaining loading slots at a warehouse for a date.

    Args:
        location: Warehouse city or code.
        date_str: Date as YYYY-MM-DD, or 'today' / 'tomorrow'.
    """
    loc = normalize_city(location)
    day = _parse_date(date_str)
    row = CAPACITY.get((loc, day))
    if row is None:
        return {
            "found": False,
            "location": loc,
            "date": day,
            "slots": 0,
            "message": "No capacity record. Treat as unknown and confirm with warehouse staff.",
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
