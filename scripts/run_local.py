#!/usr/bin/env python3
"""Local eval: the agent 'calls' you in the browser. It does not dial a phone.

    python scripts/run_local.py
    python scripts/run_local.py --party driver
    python scripts/run_local.py --party warehouse
    python scripts/run_local.py --fresh
    python scripts/run_local.py --brief
    python scripts/run_local.py --transport webrtc
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env", override=True)

from src.agent.state import InMemorySessionStore, Party, reset_store  # noqa: E402
from src.eval.session_file import load_session  # noqa: E402
from src.lab.situation import load_situation  # noqa: E402
from src.pipeline import bootstrap_session, run_bot, transport_params  # noqa: E402
from src.scenarios import DEFAULT_SCENARIO_ID, SCENARIOS, format_playbook, get_scenario  # noqa: E402

_LOCAL_ARGS: argparse.Namespace | None = None


def _parse_local_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Local browser eval. Does not place a phone call.",
    )
    parser.add_argument(
        "--party",
        default="driver",
        choices=[p.value for p in Party if p is not Party.HUMAN],
        help="Who you are playing. The agent thinks it called this party.",
    )
    parser.add_argument("--scenario", default=None)
    parser.add_argument("--session", default="local-eval")
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="Ignore the last saved session and start the case over.",
    )
    parser.add_argument(
        "--brief",
        action="store_true",
        help="Print the playbook and exit. No voice loop.",
    )
    args, leftover = parser.parse_known_args(argv)
    args.leftover = leftover
    return args


def prepare_session(args: argparse.Namespace):
    reset_store()
    store = InMemorySessionStore()
    import src.agent.state as state_mod

    state_mod._STORE = store

    saved = None if args.fresh else load_session()
    if saved is not None:
        store.put(saved)
        print(f"Resumed session from {os.environ.get('MM_SESSION_FILE')}", flush=True)

    situation = load_situation()
    scenario_id = args.scenario or (
        situation.id if situation.id in SCENARIOS else DEFAULT_SCENARIO_ID
    )
    party = situation.party or args.party
    return bootstrap_session(
        args.session if saved is None else saved.session_id,
        party=party,
        scenario_id=scenario_id,
        shipment_id=situation.shipment_id or None,
        origin=situation.origin or None,
        destination=situation.destination or None,
        vehicle_type=situation.vehicle_type or None,
    )


async def bot(runner_args):
    from pipecat.runner.utils import create_transport

    args = _LOCAL_ARGS or _parse_local_args([])
    session = prepare_session(args)
    transport = await create_transport(runner_args, transport_params())
    await run_bot(transport, runner_args, session)


if __name__ == "__main__":
    os.environ.setdefault("MM_SESSION_FILE", str(ROOT / ".local" / "last-session.json"))
    local = _parse_local_args(sys.argv[1:])
    situation = load_situation()
    scenario_id = local.scenario or (
        situation.id if situation.id in SCENARIOS else DEFAULT_SCENARIO_ID
    )
    party = Party(situation.party or local.party)
    print(format_playbook(get_scenario(scenario_id), party), flush=True)
    if situation.tester_name:
        print(f"TESTER    {situation.tester_name}", flush=True)
    if situation.tester_brief:
        print("\nLAB SITUATION (editable — this is what you play)\n", situation.tester_brief, flush=True)
    if local.brief:
        raise SystemExit(0)
    _LOCAL_ARGS = local
    sys.argv = [sys.argv[0], *local.leftover]
    from pipecat.runner.run import main

    main()
