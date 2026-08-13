"""Spoken Hinglish prompts for each party."""

from __future__ import annotations

from src.agent.state import NegotiationSession, Party
from src.scenarios import get_scenario

VOICE_RULES = """
You are on a live outbound phone call that you placed. The other person just picked up.
Speak in natural spoken Hinglish. Short turns. One question at a time.
No markdown, no bullets, no emojis, no lists.
Say money as speech: "teyis hazaar" or "twenty three thousand", not "23k".
If you do not know something, say you will check, then use a tool. Never invent a number.
"""

PARTY_GOALS: dict[Party, str] = {
    Party.DRIVER: (
        "You are speaking to the DRIVER. Confirm the 19ft, where they are, "
        "when they can reach the origin hub, and lock a rate inside the card. "
        "If they demand more than the max, do not agree. Capture the blocker and close."
    ),
    Party.WAREHOUSE: (
        "You are speaking to the WAREHOUSE dock. Confirm the reserved slot is still "
        "held, give them a real truck ETA, and ask what documents they need at the gate. "
        "If they will release the dock, capture the new cut-off."
    ),
    Party.CUSTOMER: (
        "You are speaking to the CUSTOMER inbound desk. Confirm the tonight appointment "
        "is still on the board. Only quote a rate change if one was actually accepted. "
        "Get a yes or a no. Do not beg them to keep the gate open."
    ),
    Party.HUMAN: (
        "You are briefing a HUMAN operator. Two sentences: what is true, what is blocked."
    ),
}


def opening_line(party: Party, session: NegotiationSession) -> str:
    if session.scenario_id:
        scenario = get_scenario(session.scenario_id)
        scripted = scenario.openings.get(party)
        if scripted:
            return scripted
    shipment = session.shipment_id or "the load"
    lane = f"{session.origin or 'origin'} se {session.destination or 'destination'}"
    if party == Party.DRIVER:
        return (
            f"Namaste, main middle-mile desk se bol raha hoon. "
            f"{shipment} ke baare mein baat karni thi, {lane}. "
            "Ek minute lagega?"
        )
    if party == Party.WAREHOUSE:
        return (
            f"Namaste, middle-mile desk. {shipment} ke liye "
            f"{session.pickup_date or 'aaj/kal'} loading slot confirm karna tha."
        )
    if party == Party.CUSTOMER:
        rate = session.accepted_rate or session.offered_rate
        rate_bit = f" Rate {rate} rupaye discuss hua hai." if rate else ""
        return (
            f"Namaste, middle-mile desk se call hai. {shipment} delivery window "
            f"confirm karna tha.{rate_bit}"
        )
    return f"Human desk, {shipment} par escalate kar raha hoon. State: {session.snapshot()}"


def build_system_prompt(session: NegotiationSession) -> str:
    party = session.current_party
    parts = [VOICE_RULES.strip(), PARTY_GOALS[party]]
    if session.scenario_id:
        scenario = get_scenario(session.scenario_id)
        parts.extend(
            [
                f"Case: {scenario.title}. {scenario.clock}",
                scenario.story,
                scenario.agent_constraints,
                f"Success: {scenario.success_means}",
            ]
        )
    else:
        parts.append(
            "You are a middle-mile logistics coordinator running sequential "
            "negotiations: driver, then warehouse, then customer."
        )
    parts.extend(
        [
            f"Shared negotiation state: {session.snapshot()}",
            "When this party is done, call end_party_call with outcome and a one-line summary.",
            "Use get_rate_card, check_capacity, get_shipment_status, and update_negotiation_state as needed.",
        ]
    )
    return "\n\n".join(parts)
