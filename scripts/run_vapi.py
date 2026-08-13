#!/usr/bin/env python3
"""Same-day PSTN path via Vapi while Exotel Voicebot is being wired.

    python scripts/run_vapi.py --to +9198XXXXXXXX --shipment MM-1001
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

from src.agent.coordinator import Coordinator  # noqa: E402
from src.agent.prompts import opening_line  # noqa: E402
from src.agent.state import Party  # noqa: E402
from src.telephony.vapi import VapiClient  # noqa: E402
from src.tools.status import get_shipment_status  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Vapi outbound for one party")
    parser.add_argument("--to", required=True, help="Destination number in E.164")
    parser.add_argument("--shipment", default="MM-1001")
    parser.add_argument("--session", default="vapi-dev")
    parser.add_argument("--party", default="driver", choices=[p.value for p in Party])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    info = get_shipment_status(args.shipment)
    session = Coordinator().start(
        args.session,
        shipment_id=args.shipment if info.get("found") else None,
        origin=info.get("origin") if info.get("found") else None,
        destination=info.get("destination") if info.get("found") else None,
        vehicle_type=info.get("vehicle_type") if info.get("found") else None,
        pickup_date=info.get("pickup_date") if info.get("found") else None,
        first_party=Party(args.party),
    )

    if args.dry_run:
        print(
            json.dumps(
                {
                    "to": args.to,
                    "party": session.current_party,
                    "session_id": session.session_id,
                    "first_message": opening_line(session.current_party, session),
                    "snapshot": session.snapshot(),
                },
                indent=2,
            )
        )
        return 0

    call = VapiClient().create_outbound(
        args.to,
        session=session,
        first_message=opening_line(session.current_party, session),
    )
    print(json.dumps({"id": call.id, "status": call.status}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
