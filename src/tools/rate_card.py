"""Sample price catalog. Swap this table for your own lookup."""

from __future__ import annotations

from typing import Any

ITEM_TYPES = ("half-day", "full-day", "hourly")

PRICE_LIST: dict[tuple[str, str, str], dict[str, float]] = {
    ("ANDHERI", "BANDRA", "half-day"): {"min": 7000, "typical": 8000, "max": 10000},
    ("ANDHERI", "BANDRA", "full-day"): {"min": 12000, "typical": 15000, "max": 18000},
    ("POWAI", "WORLI", "half-day"): {"min": 8000, "typical": 9000, "max": 11000},
    ("POWAI", "WORLI", "full-day"): {"min": 14000, "typical": 16000, "max": 20000},
}

ALIASES = {
    "andheri": "ANDHERI",
    "bandra": "BANDRA",
    "powai": "POWAI",
    "worli": "WORLI",
    "lightroom": "ANDHERI",
    "studio": "ANDHERI",
}


def normalize_place(name: str) -> str:
    key = name.strip().lower()
    return ALIASES.get(key, name.strip().upper())


def normalize_item(item_type: str) -> str:
    cleaned = item_type.strip().lower().replace(" ", "-")
    mapping = {
        "halfday": "half-day",
        "half-day": "half-day",
        "half": "half-day",
        "fullday": "full-day",
        "full-day": "full-day",
        "full": "full-day",
        "hourly": "hourly",
        "hour": "hourly",
    }
    return mapping.get(cleaned, cleaned)


def lookup_price(origin: str, destination: str, item_type: str) -> dict[str, Any]:
    """Return min/typical/max price for a from/to pair and item.

    Args:
        origin: Place name, e.g. "Andheri".
        destination: Place name, e.g. "Bandra".
        item_type: half-day, full-day, or hourly.
    """
    src = normalize_place(origin)
    dst = normalize_place(destination)
    item = normalize_item(item_type)
    rates = PRICE_LIST.get((src, dst, item))
    if rates is None:
        return {
            "found": False,
            "origin": src,
            "destination": dst,
            "item_type": item,
            "message": "No catalog row for this pair and item. Ask a human.",
        }
    return {
        "found": True,
        "origin": src,
        "destination": dst,
        "item_type": item,
        "currency": "INR",
        **rates,
    }


# Older name used in a few tests/scripts during the lab rewrite.
get_rate_card = lookup_price
normalize_city = normalize_place
normalize_vehicle = normalize_item
