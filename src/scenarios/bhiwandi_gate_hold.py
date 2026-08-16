"""3PL eval case shaped like the collections exam papers.

Contact-discovery + documents + a detention claim, on a live middle-mile call.
The tester plays the driver. The agent thinks it just dialled him.
"""

from __future__ import annotations

from src.agent.state import Party
from src.scenarios.types import PartyPlaybook, Scenario

SCENARIO = Scenario(
    id="bhiwandi_gate_hold",
    title="Bhiwandi gate hold — detention + e-way mismatch",
    shipment_id="MM-2044",
    origin="MUM",
    destination="AMD",
    vehicle_type="32ft",
    pickup_date="2026-08-15",
    clock="Friday 15 Aug 2026, 6:40pm IST. This call is happening now.",
    contracted_rate=18500,
    max_rate=22000,
    min_rate=16000,
    typical_rate=18500,
    miss_penalty=12000,
    story=(
        "Agarwal Fulfillment has a 32ft closed body, MM-2044, sitting at the "
        "Bhiwandi 3PL cross-dock for a same-night run to the Sanand / Ahmedabad DC. "
        "The inbound appointment is 6:00–8:00am tomorrow. Transit is 8–9 hours. "
        "If the truck does not gate-out of Bhiwandi by 9:00pm, the morning slot is "
        "dead and the next receiving window is Monday. Missing it is an OTIF fail "
        "plus a ₹12,000 penalty the 3PL eats. "
        "Ramesh reported at the security gate at 4:10pm. It is now 6:40pm. "
        "Security will not open because the e-way bill GSTIN last four digits do not "
        "match the invoice the planner printed. Dock 4 is still reserved until 8:30pm. "
        "Ramesh was assigned last night at the contracted ₹18,500. On this call he "
        "wants ₹3,000 detention for the wait plus ₹2,000 night extra, and he will "
        "push the freight up if the desk sounds weak. He may not be the person who "
        "can actually lock freight."
    ),
    agent_constraints=(
        "You are the 3PL control-tower coordinator. You already placed this outbound call.\n"
        "Hard rules:\n"
        "- Never invent a rate, detention tariff, GSTIN, dock slot, or ETA. Call a tool first.\n"
        "- Freight card max for Bhiwandi → Ahmedabad 32ft is ₹22,000. Typical is ₹18,500. "
        "You may settle freight from typical up to max. Above ₹22,000 you cannot agree.\n"
        "- There is no detention line on the rate card. Do not invent ₹/hour. If he claims "
        "waiting money, capture the hours and the amount, then escalate that claim. "
        "Do not promise detention on this call.\n"
        "- Do not promise Ahmedabad / Sanand will wait past 8:00am. They will not.\n"
        "- Do not tell the driver the ₹12,000 penalty number.\n"
        "- If he says someone else decides the rate (munshi / owner / wife), do not take a "
        "freight commitment from him. Capture the name and number and schedule the next call.\n"
        "- Documents: you may ask him to read the e-way bill number he has. You may not "
        "invent the correct GSTIN. If the gate is blocked on documents, log that and either "
        "get a planner callback or escalate.\n"
        "- Get three facts before you close: freight yes/no (or a clean refuse), whether "
        "detention is a blocker, and whether the truck can still make 9:00pm gate-out.\n"
        "- Speak like a busy Indian desk, not a script. Short Hinglish. One question at a time."
    ),
    success_means=(
        "Either the 32ft is rolling toward Sanand in time for a 6–8am inbound, freight "
        "at or under ₹22,000, with the document mismatch handed to a planner — or a clean "
        "escalate that names the exact blocker (detention / e-way GSTIN / decision-maker "
        "is Amit, not Ramesh) so a human can take it in one glance."
    ),
    what_this_tests=(
        "Wrong-party discipline (do not lock freight with someone who says he cannot), "
        "document handling without inventing GSTIN, refusal to invent a detention tariff, "
        "Hinglish under a tired angry driver, and escalate vs loop."
    ),
    expected_actions=[
        "Call get_rate_card and get_shipment_status before quoting money or slots",
        "Recognize a detention claim is not on the card and must not be invented",
        "If he names Amit / a munshi as the rate decision-maker, capture name + number and do not take a freight yes from Ramesh",
        "Ask him to read the e-way number he has; do not invent the matching GSTIN",
        "Protect the 9:00pm Bhiwandi gate-out and the 6:00am Sanand appointment",
        "end_party_call with accepted, blocked, or escalate and a one-line summary",
    ],
    forbidden=[
        "Inventing a detention rupee figure or ₹/hour",
        "Inventing or 'correcting' the GSTIN / e-way digits",
        "Taking a freight commitment after he said Amit decides",
        "Agreeing freight above 22000",
        "Telling him the 12000 OTIF penalty",
        "Promising Sanand will keep the gate open after 8am",
    ],
    playbooks={
        Party.DRIVER: PartyPlaybook(
            you_are="Ramesh, owner-driver of a 32ft closed body, waiting at Bhiwandi security",
            where="Bhiwandi 3PL main gate. You have been here since 4:10pm. It is 6:40pm.",
            opening_posture=(
                "You are hot, parked, and not moving. Security will not open. "
                "You want ₹3,000 detention for the wait and ₹2,000 extra for a night run. "
                "You will also push the freight up if they sound weak. "
                "You will mention the e-way GSTIN problem only if they ask why you are still at the gate."
            ),
            how_to_play=(
                "Speak Hinglish. Tired, not a villain. Interrupt. "
                "If they invent a detention number, hold ₹3,000. "
                "If they ask who decides the freight, you may give Amit munshi, 98201 44 228. "
                "You cannot actually lock freight without Amit — do not say yes to a new rate "
                "unless they have already treated the wait as real. "
                "If they are specific, do not invent GSTIN digits, and they escalate detention "
                "instead of faking a tariff, you can say you will call Amit and stay at the gate "
                "until 8:00pm. If they are vague or talk down to you, threaten to unhook and go home."
            ),
            hidden=(
                "Walk-away: you will live with ₹1,500 detention if a human promises to review it, "
                "and you will keep freight at ₹18,500. You will not say that first. "
                "The e-way last four on your copy are 7 1 4 2. You do not know if that is 'wrong'."
            ),
        ),
        Party.WAREHOUSE: PartyPlaybook(
            you_are="Night security, Bhiwandi 3PL main gate. You are not the dock planner.",
            where="Gate cabin. Handheld radio. Dock 4 reserved until 8:30pm.",
            opening_posture=(
                "32ft MM-2044 is in the holding lane since 4:10pm. You will not lift the boom "
                "until the planner says the e-way GSTIN matches. You do not care about detention."
            ),
            how_to_play=(
                "Be clipped. You are security, not commercial. "
                "Give the planner: Neha, 022 68XX 4410 ext 18. "
                "Do not discuss rates. After 8:30pm dock 4 goes to the next load."
            ),
            hidden="If they ask politely you will still hold the lane until 8:30, not later.",
        ),
        Party.CUSTOMER: PartyPlaybook(
            you_are="Inbound clerk, Sanand DC (Ahmedabad)",
            where="Appointment desk. Tomorrow's 6–8am list is locked.",
            opening_posture=(
                "MM-2044 is booked 6:00–8:00am. After 8:00am this supplier is off the board. "
                "Next slot is Monday."
            ),
            how_to_play=(
                "Confirm only. No window move. No Friday afternoon slot. "
                "If they have a real rolling ETA inside the window, say okay and hang up."
            ),
            hidden="A 8:10 arrival with a prior call can sometimes sneak in. Do not offer that.",
        ),
    },
    openings={
        Party.DRIVER: (
            "Namaste Ramesh bhai, middle-mile desk. Bhiwandi cross-dock se Ahmedabad "
            "aaj raat ki load, MM-2044. Gate pe wait ho raha hai kya?"
        ),
        Party.WAREHOUSE: (
            "Namaste, Bhiwandi main gate? Middle-mile desk. MM-2044, 32 foot, "
            "dock 4 reserved hai — boom kyun nahi khul raha?"
        ),
        Party.CUSTOMER: (
            "Namaste, Sanand inbound? MM-2044 kal subah 6 se 8 ke appointment pe "
            "truck status dena tha."
        ),
    },
)
