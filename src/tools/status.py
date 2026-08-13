"""Shipment status. Replace with TMS lookup later."""

from __future__ import annotations

from typing import Any

SHIPMENTS: dict[str, dict[str, Any]] = {
    "MM-1001": {
        "status": "assigned",
        "origin": "BLR",
        "destination": "HYD",
        "vehicle_type": "19ft",
        "pickup_date": "2026-08-14",
        "driver_phone": "+919800000001",
        "warehouse_phone": "+918000000001",
        "customer_phone": "+917000000001",
    },
    "MM-1002": {
        "status": "in_transit",
        "origin": "DEL",
        "destination": "MUM",
        "vehicle_type": "32ft",
        "pickup_date": "2026-08-13",
        "driver_phone": "+919800000002",
        "warehouse_phone": "+918000000002",
        "customer_phone": "+917000000002",
    },
    "MM-1003": {
        "status": "unassigned",
        "origin": "BLR",
        "destination": "CHN",
        "vehicle_type": "14ft",
        "pickup_date": "2026-08-15",
        "driver_phone": "+919800000003",
        "warehouse_phone": "+918000000003",
        "customer_phone": "+917000000003",
    },
}


def get_shipment_status(shipment_id: str) -> dict[str, Any]:
    """Look up a shipment by id.

    Args:
        shipment_id: Shipment id such as MM-1001.
    """
    key = shipment_id.strip().upper()
    row = SHIPMENTS.get(key)
    if row is None:
        return {
            "found": False,
            "shipment_id": key,
            "message": "Shipment not found.",
        }
    return {"found": True, "shipment_id": key, **row}
