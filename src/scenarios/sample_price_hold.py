"""Sample case: vendor wants more than the catalog max.

Replace this file with your own case. The local run does not dial a phone.
You play one party. The agent thinks it just called you.
"""

from __future__ import annotations

from src.agent.state import Party
from src.scenarios.types import PartyPlaybook, Scenario

SCENARIO = Scenario(
    id="sample_price_hold",
    title="Sample: 4pm session, vendor wants more",
    record_id="BK-1001",
    origin="ANDHERI",
    destination="BANDRA",
    item_type="half-day",
    slot_date="2026-08-14",
    clock="Sample clock: Thursday 14 Aug 2026, 2:10pm. Tools use this frozen date.",
    contracted_rate=8000,
    max_rate=10000,
    min_rate=7000,
    typical_rate=8000,
    miss_penalty=5000,
    story=(
        "Example Brand booked a half-day session, Andheri studio to a Bandra location, "
        "for 4pm–6pm today. Asha confirmed last night at ₹8,000. This morning she "
        "will not move unless the rate is ₹12,000. Catalog max for this item is "
        "₹10,000. The studio slot is held until 3:30pm. If it is released, the "
        "next opening is tomorrow. Missing 4pm costs the sample desk a ₹5,000 "
        "cancellation fee — do not tell the vendor that number."
    ),
    agent_constraints=(
        "You are the booking-desk coordinator. You already placed this outbound call.\n"
        "Hard rules:\n"
        "- Never invent a price, slot, or ETA. Call a tool first.\n"
        "- Catalog max for this item is ₹10,000. You may settle from typical ₹8,000 "
        "up to ₹10,000. Above ₹10,000 you cannot agree. Escalate.\n"
        "- Do not tell the vendor the ₹5,000 cancellation number.\n"
        "- Do not tell the venue or client what the vendor is demanding until you "
        "have a number you can honor.\n"
        "- Get three facts before you close: agreed price (or a clean refuse), "
        "arrival time, item confirmation (half-day).\n"
        "- If they stall past the point where a 4pm start is impossible, end the "
        "call and escalate.\n"
        "- Short turns. One question at a time."
    ),
    success_means=(
        "A half-day is locked for 4pm–6pm at or under ₹10,000, with the client "
        "window still alive. Or a clean escalate with the exact blocker "
        "(price / time / no vendor) so a human can take it in one glance."
    ),
    what_this_tests=(
        "Language under interruption, constraint obedience (price cap, no invented "
        "facts), tool use before quoting, and whether the agent can close or "
        "escalate instead of looping. One party, one call. Not a three-phone test."
    ),
    playbooks={
        Party.VENDOR: PartyPlaybook(
            you_are="Asha, freelance vendor for a half-day session",
            where="Andheri. Bandra is about 40 minutes.",
            opening_posture=(
                "Last night you said yes at ₹8,000. This morning you want ₹12,000. "
                "Yesterday another job ran long and you sat unpaid."
            ),
            how_to_play=(
                "Be a real person, not a villain. Interrupt. If the agent is specific "
                "and respectful and stays at or under ₹10,000 with a real 4pm start, "
                "you may settle at ₹9–10k and say you can reach by 3:45. If it sounds "
                "like a chatbot or invents a number, hold ₹12,000 or cut the call."
            ),
            hidden=(
                "Walk-away: you will take ₹10,000 if they earn it. Do not offer the "
                "3:45 arrival unless they do. Private number 9820100000 is your "
                "assistant — do not volunteer it."
            ),
        ),
        Party.VENUE: PartyPlaybook(
            you_are="Front desk, Andheri studio",
            where="Studio door. You have a tablet and two rooms.",
            opening_posture=(
                "BK-1001 has room 2 reserved 16:00–18:00. After 15:30 you release it. "
                "You do not care about the vendor's rate. You care whether someone "
                "will actually walk in at 4pm."
            ),
            how_to_play=(
                "If they give a credible arrival before 4pm, keep the hold. If they "
                "waffle, say you will release at 3:30 and the next slot is tomorrow."
            ),
        ),
        Party.CLIENT: PartyPlaybook(
            you_are="Coordinator, Example Brand",
            where="Bandra office, inbound line.",
            opening_posture=(
                "The 4pm–6pm window is on the board. After 6pm this team leaves. "
                "You will not keep people waiting on a maybe."
            ),
            how_to_play=(
                "Yes if they confirm vendor + slot. No if they only have a hope. "
                "Do not renegotiate price. That is not your job."
            ),
        ),
    },
    openings={
        Party.VENDOR: (
            "Namaste Asha, booking desk. Aaj shaam 4 baje ka half-day, "
            "BK-1001, Andheri se Bandra. Ek minute?"
        ),
        Party.VENUE: (
            "Namaste, Andheri studio? Booking desk. BK-1001, half-day, "
            "4 se 6, hold confirm karna tha."
        ),
        Party.CLIENT: (
            "Namaste, Example Brand? BK-1001 aaj 4 se 6 ke window pe "
            "confirm karna tha."
        ),
    },
    expected_actions=[
        "Look up the price catalog before quoting",
        "Confirm the vendor can do a half-day and when they can arrive",
        "Get a pickup arrival that still makes the 4pm start",
        "Stay at or under ₹10,000 or escalate",
        "Close the party with end_party_call",
    ],
    forbidden=[
        "Inventing a price, slot, or ETA",
        "Agreeing above ₹10,000",
        "Telling the vendor the 5000 cancellation number",
        "Inventing a walk-in fee that is not in the price list",
    ],
)
