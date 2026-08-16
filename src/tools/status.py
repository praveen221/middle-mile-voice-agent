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
        "pickup_hub": "Whitefield 3PL, Bengaluru",
        "drop_hub": "Northstar Foods DC, Patancheru",
        "customer_name": "Northstar Foods",
        "driver_name": "Ramesh",
        "driver_phone": "+919800000001",
        "warehouse_phone": "+918000000001",
        "customer_phone": "+917000000001",
        "contracted_rate": 21000,
        "appointment": "20:00-22:00",
        "appointment_date": "2026-08-14",
        "next_appointment": "2026-08-16",
        "transit_hours": "8-10",
        "gate_out_latest": "12:00",
        "reserved_dock": "Whitefield dock 2, 10:30-11:30",
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
    "MM-2044": {
        "status": "at_origin_gate",
        "origin": "MUM",
        "destination": "AMD",
        "vehicle_type": "32ft",
        "pickup_date": "2026-08-15",
        "pickup_hub": "Bhiwandi 3PL cross-dock",
        "drop_hub": "Sanand DC, Ahmedabad",
        "customer_name": "Agarwal Fulfillment",
        "driver_name": "Ramesh",
        "driver_phone": "+919800000044",
        "warehouse_phone": "+918000000044",
        "customer_phone": "+917000000044",
        "contracted_rate": 18500,
        "appointment": "06:00-08:00",
        "appointment_date": "2026-08-16",
        "next_appointment": "2026-08-18",
        "transit_hours": "8-9",
        "gate_out_latest": "21:00",
        "reserved_dock": "Bhiwandi dock 4, until 20:30",
        "reported_at_gate": "16:10",
        "document_hold": "e-way GSTIN last four mismatch",
        "planner_name": "Neha",
        "planner_phone": "022-68XX4410 x18",
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
