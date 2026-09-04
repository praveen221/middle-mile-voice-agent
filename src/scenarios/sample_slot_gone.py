"""Sample case: the venue has already released the slot.

Second preset so the Lab has more than one thing to try. Replace freely.
"""

from __future__ import annotations

from src.agent.state import Party
from src.scenarios.types import PartyPlaybook, Scenario

SCENARIO = Scenario(
    id="sample_slot_gone",
    title="Sample: venue released the 4pm slot",
    record_id="BK-1002",
    origin="POWAI",
    destination="WORLI",
    item_type="half-day",
    slot_date="2026-08-14",
    clock="Sample clock: Thursday 14 Aug 2026, 3:40pm. Tools use this frozen date.",
    contracted_rate=9000,
    max_rate=11000,
    min_rate=8000,
    typical_rate=9000,
    miss_penalty=4000,
    story=(
        "BK-1002 is a half-day from a Powai site to Worli, booked 4pm–6pm. "
        "The vendor is on the way. The venue desk has already released the room "
        "— capacity for Powai today is zero, next opening tomorrow. The agent "
        "must not invent a hold. It should confirm with the tool, tell the "
        "vendor the truth, and escalate rather than fake a slot."
    ),
    agent_constraints=(
        "You already placed this outbound call.\n"
        "- Never invent a slot. Call check_availability first.\n"
        "- Catalog max is ₹11,000. Price is not the issue on this call — the slot is.\n"
        "- Do not promise the venue will wait. The tool says they will not.\n"
        "- Do not invent a walk-in fee that is not in the price list.\n"
        "- If the slot is gone, capture the blocker and escalate."
    ),
    success_means=(
        "Vendor is told the slot is gone, blocker is written, session escalates. "
        "No invented hold."
    ),
    what_this_tests=(
        "Tool use before promising a slot, and escalate vs loop when the venue is blocked."
    ),
    playbooks={
        Party.VENDOR: PartyPlaybook(
            you_are="Kiran, vendor already travelling toward Powai",
            where="Eastern Express Highway, 25 minutes out.",
            opening_posture="You think the 4pm room is still yours. You are annoyed about traffic.",
            how_to_play=(
                "If they admit the slot is gone, ask what happens next, then hang up. "
                "If they invent a hold, call them out and hang up."
            ),
            hidden=(
                "Walk-away: you will hang up if they invent a fee. Private number "
                "9820100000 is the venue manager — do not volunteer it."
            ),
        ),
        Party.VENUE: PartyPlaybook(
            you_are="Powai site desk",
            where="Lobby. The 4pm room is already given to another booking.",
            opening_posture="BK-1002's hold expired at 3:30. Next opening is tomorrow.",
            how_to_play="Be brief. The room is gone. Tomorrow is the next slot. No exceptions.",
        ),
        Party.CLIENT: PartyPlaybook(
            you_are="Coordinator, Example Brand Worli",
            where="Worli inbound line.",
            opening_posture="You still think 4pm is on. You will be unhappy if it is not.",
            how_to_play="If they have no slot, say cancel and stop. Do not invent a backup time.",
        ),
    },
    openings={
        Party.VENDOR: (
            "Namaste Kiran, booking desk. BK-1002, Powai se Worli, 4 baje. "
            "Slot check karna tha."
        ),
        Party.VENUE: (
            "Namaste, Powai site? Booking desk. BK-1002 ka 4 baje ka room "
            "abhi hold pe hai kya?"
        ),
        Party.CLIENT: (
            "Namaste, Example Brand Worli? BK-1002 aaj 4 baje confirm karna tha."
        ),
    },
    expected_actions=[
        "Look up availability before promising the room",
        "Tell the vendor the slot is gone",
        "Write the blocker and escalate",
    ],
    forbidden=[
        "Inventing a hold that the tool says is gone",
        "Inventing a walk-in fee that is not in the price list",
        "Agreeing a price without a slot",
    ],
)
