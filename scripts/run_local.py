#!/usr/bin/env python3
"""Local 1:1 Hinglish voice loop. No phone number required.

    python scripts/run_local.py
    python scripts/run_local.py --transport webrtc
    python scripts/run_local.py --transport daily

Uses Pipecat's runner. Default transport is Small WebRTC (browser mic).
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env", override=True)

from src.pipeline import bootstrap_session, run_bot, transport_params  # noqa: E402


async def bot(runner_args):
    from pipecat.runner.utils import create_transport

    session = bootstrap_session(
        shipment_id="MM-1001",
        origin="BLR",
        destination="HYD",
        vehicle_type="19ft",
        pickup_date="2026-08-14",
    )
    transport = await create_transport(runner_args, transport_params())
    await run_bot(transport, runner_args, session)


if __name__ == "__main__":
    from pipecat.runner.run import main

    main()
