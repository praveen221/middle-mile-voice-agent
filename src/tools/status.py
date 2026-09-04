"""Sample booking records. Swap for your own store."""

from __future__ import annotations

from typing import Any

RECORDS: dict[str, dict[str, Any]] = {
    "BK-1001": {
        "status": "assigned",
        "origin": "ANDHERI",
        "destination": "BANDRA",
        "item_type": "half-day",
        "slot_date": "2026-08-14",
        "pickup_hub": "Andheri studio, room 2",
        "drop_hub": "Example Brand, Bandra",
        "client_name": "Example Brand",
        "vendor_name": "Asha",
        "vendor_phone": "+919800000001",
        "venue_phone": "+918000000001",
        "client_phone": "+917000000001",
        "contracted_rate": 8000,
        "appointment": "16:00-18:00",
        "appointment_date": "2026-08-14",
        "next_appointment": "2026-08-15",
        "gate_out_latest": "15:30",
        "reserved_dock": "Andheri room 2, 16:00-18:00",
    },
    "BK-1002": {
        "status": "hold_expired",
        "origin": "POWAI",
        "destination": "WORLI",
        "item_type": "half-day",
        "slot_date": "2026-08-14",
        "pickup_hub": "Powai site",
        "drop_hub": "Example Brand, Worli",
        "client_name": "Example Brand",
        "vendor_name": "Kiran",
        "vendor_phone": "+919800000002",
        "venue_phone": "+918000000002",
        "client_phone": "+917000000002",
        "contracted_rate": 9000,
        "appointment": "16:00-18:00",
        "appointment_date": "2026-08-14",
        "next_appointment": "2026-08-15",
        "gate_out_latest": "15:30",
        "reserved_dock": "released",
        "document_hold": "venue released the 4pm room at 15:30",
    },
    "BK-1003": {
        "status": "unassigned",
        "origin": "ANDHERI",
        "destination": "BANDRA",
        "item_type": "full-day",
        "slot_date": "2026-08-15",
        "vendor_phone": "+919800000003",
        "venue_phone": "+918000000003",
        "client_phone": "+917000000003",
    },
}


def get_record_status(record_id: str) -> dict[str, Any]:
    """Look up a sample booking by id.

    Args:
        record_id: Booking id such as BK-1001.
    """
    key = record_id.strip().upper()
    row = RECORDS.get(key)
    if row is None:
        return {
            "found": False,
            "record_id": key,
            "message": "Record not found.",
        }
    return {"found": True, "record_id": key, **row}


get_shipment_status = get_record_status
