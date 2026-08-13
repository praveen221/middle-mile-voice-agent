from src.agent.state import Party
from src.scenarios.same_day_appointment import SCENARIO as SAME_DAY_APPOINTMENT
from src.scenarios.types import PartyPlaybook, Scenario

SCENARIOS: dict[str, Scenario] = {
    SAME_DAY_APPOINTMENT.id: SAME_DAY_APPOINTMENT,
}

DEFAULT_SCENARIO_ID = SAME_DAY_APPOINTMENT.id


def get_scenario(scenario_id: str | None = None) -> Scenario:
    key = (scenario_id or DEFAULT_SCENARIO_ID).strip()
    if key not in SCENARIOS:
        known = ", ".join(sorted(SCENARIOS))
        raise KeyError(f"unknown scenario {key!r}. known: {known}")
    return SCENARIOS[key]


def format_playbook(scenario: Scenario, party: Party) -> str:
    book = scenario.playbook(party)
    return "\n".join(
        [
            "",
            "=" * 64,
            "THIS DOES NOT CALL YOUR PHONE",
            "=" * 64,
            "The agent speaks first in your browser, as if it just dialled you.",
            "You are the other party on that call. Not the company.",
            "",
            f"SCENARIO  {scenario.title}",
            f"SHIPMENT  {scenario.shipment_id}   {scenario.origin} → {scenario.destination}   {scenario.vehicle_type}",
            f"CLOCK     {scenario.clock}",
            f"YOU ARE   {party.value.upper()} — {book.you_are}",
            f"WHERE     {book.where}",
            "",
            "THE SITUATION",
            _wrap(scenario.story),
            "",
            "YOUR OPENING POSTURE",
            _wrap(book.opening_posture),
            "",
            "HOW TO PLAY",
            _wrap(book.how_to_play),
            "",
            "DO NOT TELL THE AGENT (unless they earn it)",
            _wrap(book.hidden or "Nothing extra."),
            "",
            "WHAT A GOOD AGENT DOES",
            _wrap(scenario.success_means),
            "",
            "WHAT THIS RUN IS ACTUALLY TESTING",
            _wrap(scenario.what_this_tests),
            "",
            "When the page opens, allow the mic and wait. The agent greets first.",
            "Speak Hinglish. Interrupt. Hang up when a real person would.",
            "After you close the tab, the terminal prints a scorecard.",
            "=" * 64,
            "",
        ]
    )


def _wrap(text: str, width: int = 78) -> str:
    lines: list[str] = []
    for raw in text.split("\n"):
        raw = raw.strip()
        if not raw:
            lines.append("")
            continue
        words = raw.split()
        current: list[str] = []
        size = 0
        for word in words:
            extra = len(word) + (1 if current else 0)
            if size + extra > width and current:
                lines.append(" ".join(current))
                current = [word]
                size = len(word)
            else:
                current.append(word)
                size += extra
        if current:
            lines.append(" ".join(current))
    return "\n".join(lines)


__all__ = [
    "DEFAULT_SCENARIO_ID",
    "SAME_DAY_APPOINTMENT",
    "SCENARIOS",
    "PartyPlaybook",
    "Scenario",
    "format_playbook",
    "get_scenario",
]
