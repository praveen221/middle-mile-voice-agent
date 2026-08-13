#!/usr/bin/env python3
"""Smoke-test the in-process tools without a voice stack."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.agent.coordinator import Coordinator
from src.agent.state import PartyOutcome
from src.tools.capacity import check_capacity
from src.tools.rate_card import get_rate_card
from src.tools.status import get_shipment_status


def show(title: str, payload: object) -> None:
    print(f"\n== {title} ==")
    print(json.dumps(payload, indent=2, default=str))


def main() -> int:
    show("rate_card BLR-HYD 19ft", get_rate_card("Bangalore", "Hyderabad", "19ft"))
    show("rate_card missing lane", get_rate_card("Goa", "Kochi", "14ft"))
    show("capacity BLR tomorrow", check_capacity("BLR", "tomorrow"))
    show("capacity MUM today-ish", check_capacity("Mumbai", "2026-08-14"))
    show("shipment MM-1001", get_shipment_status("mm-1001"))

    coordinator = Coordinator()
    session = coordinator.start(
        "tool-smoke",
        shipment_id="MM-1001",
        origin="BLR",
        destination="HYD",
        vehicle_type="19ft",
        pickup_date="2026-08-14",
    )
    decision = coordinator.record_party_end(
        session.session_id,
        outcome=PartyOutcome.ACCEPTED,
        summary="Driver agreed 21000 on a 19ft.",
        rate=21000,
    )
    show("after driver accepted", {"decision": decision.model_dump(), "snapshot": coordinator.get(session.session_id).snapshot()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
