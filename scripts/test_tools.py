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
from src.tools.capacity import check_availability
from src.tools.rate_card import lookup_price
from src.tools.status import get_record_status


def show(title: str, payload: object) -> None:
    print(f"\n== {title} ==")
    print(json.dumps(payload, indent=2, default=str))


def main() -> int:
    show("price Andheri-Bandra half-day", lookup_price("Andheri", "Bandra", "half-day"))
    show("price missing pair", lookup_price("Goa", "Kochi", "hourly"))
    show("availability Andheri tomorrow", check_availability("ANDHERI", "tomorrow"))
    show("availability Powai today-ish", check_availability("Powai", "2026-08-14"))
    show("record BK-1001", get_record_status("bk-1001"))

    coordinator = Coordinator()
    session = coordinator.start(
        "tool-smoke",
        record_id="BK-1001",
        origin="ANDHERI",
        destination="BANDRA",
        item_type="half-day",
        slot_date="2026-08-14",
    )
    decision = coordinator.record_party_end(
        session.session_id,
        outcome=PartyOutcome.ACCEPTED,
        summary="Vendor agreed 9000 on a half-day.",
        rate=9000,
    )
    show(
        "after vendor accepted",
        {"decision": decision.model_dump(), "snapshot": coordinator.get(session.session_id).snapshot()},
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
