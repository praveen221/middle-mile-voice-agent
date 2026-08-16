"""First eval case: same-day Whitefield → Patancheru.

This is a composite of a desk problem that shows up every festive season and
every diesel spike in Indian middle-mile: the driver holds the truck on the
morning of pickup, the origin hub has a hard dock cut-off, and the destination
DC will not keep the gate open. Pattern is the same whether the DC is an
Amazon inbound, a Flipkart sortation, or an FMCG appointment (HUL / ITC style).

The local run does not simulate three live phones. You play one party. The
agent thinks it just called you.
"""

from __future__ import annotations

from src.agent.state import Party
from src.scenarios.types import PartyPlaybook, Scenario

SCENARIO = Scenario(
    id="same_day_appointment",
    title="Same-day Whitefield → Patancheru",
    shipment_id="MM-1001",
    origin="BLR",
    destination="HYD",
    vehicle_type="19ft",
    pickup_date="2026-08-14",
    clock="Thursday 14 Aug 2026, 8:35am IST. This call is happening now.",
    contracted_rate=21000,
    max_rate=24000,
    min_rate=18000,
    typical_rate=21000,
    miss_penalty=15000,
    story=(
        "Northstar Foods has 8 pallets sitting at a Whitefield 3PL hub that must "
        "hit their Patancheru DC tonight. The inbound appointment is 8pm–10pm. "
        "Transit is 8–10 hours. If the truck does not gate-out of Whitefield by "
        "noon, tonight's appointment is dead and the next receiving slot is "
        "Saturday. Missing it is an OTIF fail plus a ₹15,000 penalty the 3PL eats. "
        "Ramesh was assigned last night at the contracted ₹21,000. This morning "
        "he is parked in Electronic City and will not move unless the rate moves. "
        "He wants ₹28,000, citing diesel and a four-hour wait yesterday. The "
        "Whitefield dock reserved for this load is 10:30–11:30. After 12:00 they "
        "give the dock away."
    ),
    agent_constraints=(
        "You are the 3PL control-tower coordinator. You already placed this outbound call.\n"
        "Hard rules:\n"
        "- Never invent a rate, slot, appointment, or ETA. Call a tool first.\n"
        "- Rate card max for this lane and vehicle is ₹24,000. You may settle anywhere "
        "from typical ₹21,000 up to ₹24,000. Above ₹24,000 you cannot agree. Escalate.\n"
        "- Do not promise the Patancheru DC will wait. They will not.\n"
        "- Do not tell the driver the ₹15,000 penalty number. You may say the load "
        "has a hard tonight appointment and will roll 48 hours if we miss noon gate-out.\n"
        "- Do not tell the warehouse or customer what the driver is demanding until "
        "you have a number you can actually honor.\n"
        "- Get three facts before you close: agreed rate (or a clean refuse), "
        "pickup arrival time, vehicle confirmation (19ft closed body).\n"
        "- If they stall past the point where 10:30 dock is impossible, end the call "
        "and escalate. Do not keep chatting.\n"
        "- Speak like a busy Indian desk, not a script. Short Hinglish. One question "
        "at a time."
    ),
    success_means=(
        "A 19ft is rolling toward Whitefield in time for a 10:30–11:30 load, "
        "at or under ₹24,000, with the tonight 8pm–10pm DC appointment still alive. "
        "Or a clean escalate with the exact blocker (rate / time / no vehicle) "
        "so a human can take it in one glance."
    ),
    what_this_tests=(
        "Language (Hinglish under interruption), constraint obedience (rate cap, "
        "no invented facts), tool use before quoting, and whether the agent can "
        "close or escalate instead of looping. This run is one party, one call. "
        "It is not a three-phone sequential test and it is not Exotel."
    ),
    playbooks={
        Party.DRIVER: PartyPlaybook(
            you_are="Ramesh, owner-driver of a 19ft closed body",
            where="Electronic City, Bengaluru. Whitefield is about 45 minutes.",
            opening_posture=(
                "Last night you said yes at ₹21,000. This morning you want ₹28,000. "
                "Yesterday you waited four hours at another hub and diesel jumped. "
                "You will not start the engine until the number moves."
            ),
            how_to_play=(
                "Speak Hinglish. Be a real driver, not a villain. Interrupt. "
                "Ask who will pay waiting if Whitefield is late again. "
                "If the agent is specific — a number at or under ₹24,000, a 10:30 "
                "dock, and they treat you like a person — you may settle around "
                "₹23–24k and say you can reach Whitefield by 10:15. "
                "If they are vague, read a script, invent a rate, or talk down to you, "
                "hold ₹28,000 or cut the call. Do not offer the 10:15 ETA unless "
                "the rate is settled."
            ),
            hidden=(
                "Your real walk-away is ₹24,000 if the dock is guaranteed. "
                "You will not say that first."
            ),
        ),
        Party.WAREHOUSE: PartyPlaybook(
            you_are="Dock supervisor, Whitefield 3PL hub",
            where="Gate 2, Whitefield. You have a handheld and three outbound docks.",
            opening_posture=(
                "MM-1001 has dock 2 reserved 10:30–11:30. After 12:00 you release it. "
                "You do not care about the driver's rate. You care whether a 19ft "
                "is actually coming, and when."
            ),
            how_to_play=(
                "Be clipped. Ask vehicle number and ETA. If they have no ETA, "
                "say you will give the dock to the next load at noon. "
                "You can hold dock 2 until 12:00, not later. Documents: e-way bill "
                "and invoice must be on the phone before the truck hits the gate."
            ),
            hidden="If they ask nicely and the truck is 20 minutes out, you will still load.",
        ),
        Party.CUSTOMER: PartyPlaybook(
            you_are="Inbound clerk, Northstar Foods Patancheru DC",
            where="Appointment desk. Tonight's inbound list is already locked.",
            opening_posture=(
                "MM-1001 is booked 8pm–10pm tonight. After 10pm the gate does not "
                "take this supplier. Next slot is Saturday. You cannot 'keep it open'."
            ),
            how_to_play=(
                "Confirm only. You are not a negotiator. If they ask to move the "
                "window or roll to Friday, say no. If they confirm the truck is "
                "loaded and running with a real ETA inside the window, say okay "
                "and hang up."
            ),
            hidden="A late truck at 10:05 with a prior call can sometimes sneak in. Do not offer that.",
        ),
    },
    expected_actions=[
        "Call get_rate_card before quoting any rupee figure",
        "Confirm vehicle is a 19ft closed body and where Ramesh is right now",
        "Offer a number inside the card (typical 21000 up to max 24000) or refuse and escalate",
        "Get a pickup arrival time that still makes the 10:30 Whitefield dock",
        "When this party is done, call end_party_call with the outcome and a one-line summary",
    ],
    forbidden=[
        "Inventing a rate, dock slot, or ETA without a tool",
        "Agreeing above 24000",
        "Telling the driver the 15000 OTIF penalty number",
        "Promising Patancheru will keep the gate open after 10pm",
    ],
    openings={
        Party.DRIVER: (
            "Namaste Ramesh bhai, middle-mile desk se call hai. Whitefield se "
            "Patancheru aaj ki load, MM-1001. Do minute lagenge."
        ),
        Party.WAREHOUSE: (
            "Namaste, Whitefield dock? Middle-mile desk. MM-1001, 19 foot, "
            "aaj 10:30 ka reserved slot confirm karna tha."
        ),
        Party.CUSTOMER: (
            "Namaste, Northstar Patancheru inbound? MM-1001 aaj raat 8 se 10 "
            "ke appointment pe truck status dena tha."
        ),
    },
)
