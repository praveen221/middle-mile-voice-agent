"""Lane + vehicle rate cards. Replace the table with your live TMS later."""

from __future__ import annotations

from typing import Any

VEHICLE_TYPES = ("pickup", "407", "14ft", "17ft", "19ft", "22ft", "32ft")

# Typical one-way INR for demo lanes. min/max are negotiate bounds.
RATE_CARD: dict[tuple[str, str, str], dict[str, float]] = {
    ("BLR", "HYD", "14ft"): {"min": 14000, "typical": 16500, "max": 19000},
    ("BLR", "HYD", "19ft"): {"min": 18000, "typical": 21000, "max": 24000},
    ("BLR", "HYD", "32ft"): {"min": 26000, "typical": 30000, "max": 34000},
    ("BLR", "CHN", "14ft"): {"min": 12000, "typical": 14500, "max": 17000},
    ("BLR", "CHN", "19ft"): {"min": 16000, "typical": 19000, "max": 22000},
    ("DEL", "MUM", "19ft"): {"min": 28000, "typical": 33000, "max": 38000},
    ("DEL", "MUM", "32ft"): {"min": 40000, "typical": 46000, "max": 52000},
    ("MUM", "PUN", "14ft"): {"min": 7000, "typical": 8500, "max": 10000},
    ("MUM", "AMD", "32ft"): {"min": 16000, "typical": 18500, "max": 22000},
    ("MUM", "AMD", "19ft"): {"min": 12000, "typical": 14500, "max": 17000},
    ("HYD", "VIZ", "19ft"): {"min": 15000, "typical": 17500, "max": 20000},
}

ALIASES = {
    "bangalore": "BLR",
    "bengaluru": "BLR",
    "blr": "BLR",
    "hyderabad": "HYD",
    "hyd": "HYD",
    "chennai": "CHN",
    "chn": "CHN",
    "madras": "CHN",
    "delhi": "DEL",
    "del": "DEL",
    "ncr": "DEL",
    "mumbai": "MUM",
    "bom": "MUM",
    "mum": "MUM",
    "pune": "PUN",
    "pun": "PUN",
    "vizag": "VIZ",
    "visakhapatnam": "VIZ",
    "viz": "VIZ",
    "whitefield": "BLR",
    "patancheru": "HYD",
    "electroniccity": "BLR",
    "bhiwandi": "MUM",
    "ahmedabad": "AMD",
    "amd": "AMD",
    "sanand": "AMD",
}


def normalize_city(name: str) -> str:
    key = name.strip().lower()
    return ALIASES.get(key, name.strip().upper())


def normalize_vehicle(vehicle_type: str) -> str:
    cleaned = vehicle_type.strip().lower().replace(" ", "")
    mapping = {
        "tata407": "407",
        "407": "407",
        "14foot": "14ft",
        "14ft": "14ft",
        "17ft": "17ft",
        "19ft": "19ft",
        "22ft": "22ft",
        "32ft": "32ft",
        "pickup": "pickup",
        "ace": "pickup",
    }
    return mapping.get(cleaned, cleaned)


def get_rate_card(origin: str, destination: str, vehicle_type: str) -> dict[str, Any]:
    """Return min/typical/max rate for a lane and vehicle.

    Args:
        origin: City or code, e.g. "Bangalore" or "BLR".
        destination: City or code, e.g. "Hyderabad".
        vehicle_type: One of pickup, 407, 14ft, 17ft, 19ft, 22ft, 32ft.
    """
    src = normalize_city(origin)
    dst = normalize_city(destination)
    vehicle = normalize_vehicle(vehicle_type)
    rates = RATE_CARD.get((src, dst, vehicle))
    if rates is None:
        return {
            "found": False,
            "origin": src,
            "destination": dst,
            "vehicle_type": vehicle,
            "message": "No rate card for this lane and vehicle. Ask a human.",
        }
    return {
        "found": True,
        "origin": src,
        "destination": dst,
        "vehicle_type": vehicle,
        "currency": "INR",
        **rates,
    }
