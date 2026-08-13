#!/usr/bin/env python3
"""Place a real Exotel outbound call, then (optionally) keep calling the next party.

    python scripts/run_outbound.py --to +9198XXXXXXXX --shipment MM-1001
    python scripts/run_outbound.py --to +9198XXXXXXXX --party driver --session mm-demo-1

The Exotel Voicebot applet / SIP trunk still has to land in the Pipecat pipeline.
This script owns the *sequencing*: hang up → decide → dial next number.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env", override=True)

from src.agent.coordinator import Coordinator, NextAction  # noqa: E402
from src.agent.state import Party  # noqa: E402
from src.telephony.exotel import ExotelClient  # noqa: E402
from src.tools.status import get_shipment_status  # noqa: E402


def _party_number(shipment: dict, party: Party) -> str | None:
    return {
        Party.DRIVER: shipment.get("driver_phone"),
        Party.WAREHOUSE: shipment.get("warehouse_phone"),
        Party.CUSTOMER: shipment.get("customer_phone"),
    }.get(party)


def main() -> int:
    parser = argparse.ArgumentParser(description="Exotel outbound for one party")
    parser.add_argument("--to", help="Override destination number (E.164)")
    parser.add_argument("--shipment", default="MM-1001")
    parser.add_argument("--session", default="outbound-dev")
    parser.add_argument("--party", default="driver", choices=[p.value for p in Party])
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the Exotel payload without placing the call",
    )
    args = parser.parse_args()

    info = get_shipment_status(args.shipment)
    coordinator = Coordinator()
    session = coordinator.start(
        args.session,
        shipment_id=args.shipment if info.get("found") else None,
        origin=info.get("origin") if info.get("found") else None,
        destination=info.get("destination") if info.get("found") else None,
        vehicle_type=info.get("vehicle_type") if info.get("found") else None,
        pickup_date=info.get("pickup_date") if info.get("found") else None,
        first_party=Party(args.party),
    )

    to_number = args.to
    if not to_number and info.get("found"):
        to_number = _party_number(info, session.current_party)
    if not to_number:
        print("No destination number. Pass --to or use a known shipment id.", file=sys.stderr)
        return 2

    client = ExotelClient()
    payload = {
        "to": to_number,
        "party": session.current_party,
        "session_id": session.session_id,
        "flow_url": None if args.dry_run and not client.settings.exotel_app_id else None,
        "snapshot": session.snapshot(),
    }
    if args.dry_run:
        try:
            payload["flow_url"] = client.flow_url()
            payload["caller_id"] = client.settings.exotel_from_number
            payload["base_url"] = client.base_url
        except Exception as exc:  # noqa: BLE001 — dry-run should still print
            payload["config_error"] = str(exc)
        print(json.dumps(payload, indent=2))
        return 0

    call = client.connect_to_flow(
        to_number,
        custom_field=json.dumps(
            {"session_id": session.session_id, "party": session.current_party.value}
        ),
    )
    print(json.dumps({"call_sid": call.sid, "status": call.status, **payload}, indent=2, default=str))
    print(
        "After this leg ends, inspect coordinator state and dial the next party "
        f"(actions: {[a.value for a in NextAction]})."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
