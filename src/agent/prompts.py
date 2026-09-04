"""Spoken prompts for each party. Sample case is Hinglish; Lab language is yours."""

from __future__ import annotations

from src.agent.state import NegotiationSession, Party
from src.scenarios import get_scenario

VOICE_RULES = """
You are on a live outbound phone call that you placed. The other person just picked up.
Speak in natural spoken language (the sample case is Hinglish). Short turns. One question at a time.
No markdown, no bullets, no emojis, no lists.
Say money as speech: "das hazaar" or "ten thousand", not "10k".
If you do not know something, say you will check, then use a tool. Never invent a number.
"""

PARTY_GOALS: dict[Party, str] = {
    Party.VENDOR: (
        "You are speaking to the VENDOR. Confirm they can do the job, when they "
        "can arrive, and lock a price inside the catalog. If they demand more "
        "than the max, do not agree. Capture the blocker and close."
    ),
    Party.VENUE: (
        "You are speaking to the VENUE desk. Confirm the reserved slot is still "
        "held, give them a real arrival time, and ask what they need at the door. "
        "If they will release the slot, capture the new cut-off."
    ),
    Party.CLIENT: (
        "You are speaking to the CLIENT desk. Confirm today's appointment is "
        "still on. Only quote a price change if one was actually accepted. "
        "Get a yes or a no."
    ),
    Party.HUMAN: (
        "You are briefing a HUMAN operator. Two sentences: what is true, what is blocked."
    ),
}


def opening_line(party: Party, session: NegotiationSession, situation=None) -> str:
    if situation is not None and getattr(situation, "opening_line", ""):
        return situation.opening_line
    if session.scenario_id:
        scenario = get_scenario(session.scenario_id)
        scripted = scenario.openings.get(party)
        if scripted:
            return scripted
    record = session.record_id or "the booking"
    lane = f"{session.origin or 'origin'} se {session.destination or 'destination'}"
    if party == Party.VENDOR:
        return (
            f"Namaste, main booking desk se bol raha hoon. "
            f"{record} ke baare mein baat karni thi, {lane}. "
            "Ek minute lagega?"
        )
    if party == Party.VENUE:
        return (
            f"Namaste, booking desk. {record} ke liye "
            f"{session.slot_date or 'aaj/kal'} slot confirm karna tha."
        )
    if party == Party.CLIENT:
        rate = session.accepted_rate or session.offered_rate
        rate_bit = f" Rate {rate} rupaye discuss hua hai." if rate else ""
        return (
            f"Namaste, booking desk se call hai. {record} window "
            f"confirm karna tha.{rate_bit}"
        )
    return f"Human desk, {record} par escalate kar raha hoon. State: {session.snapshot()}"


def build_system_prompt(session: NegotiationSession, situation=None) -> str:
    party = session.current_party
    parts = [VOICE_RULES.strip(), PARTY_GOALS[party]]
    if situation is not None:
        parts.extend(
            [
                f"Case: {situation.title}. {situation.clock}".strip(),
                situation.story,
                situation.agent_constraints,
            ]
        )
        if situation.expected_actions:
            parts.append("Expected on this call:\n- " + "\n- ".join(situation.expected_actions))
        if situation.forbidden:
            parts.append("Forbidden:\n- " + "\n- ".join(situation.forbidden))
        parts.append(f"Success: {situation.success_means}")
    elif session.scenario_id:
        scenario = get_scenario(session.scenario_id)
        parts.extend(
            [
                f"Case: {scenario.title}. {scenario.clock}",
                scenario.story,
                scenario.agent_constraints,
            ]
        )
        if scenario.expected_actions:
            parts.append("Expected on this call:\n- " + "\n- ".join(scenario.expected_actions))
        if scenario.forbidden:
            parts.append("Forbidden:\n- " + "\n- ".join(scenario.forbidden))
        parts.append(f"Success: {scenario.success_means}")
    else:
        parts.append(
            "You are a booking desk running sequential calls: vendor, then venue, then client."
        )
    parts.extend(
        [
            f"Shared negotiation state: {session.snapshot()}",
            "When this party is done, call end_party_call with outcome and a one-line summary.",
            "Use lookup_price, check_availability, get_record_status, and update_negotiation_state as needed.",
        ]
    )
    return "\n\n".join(parts)
