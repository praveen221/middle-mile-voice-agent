"""Editable call situation. Saved on disk, injected into the prompt, stored on the call row."""

from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel, Field

from src.agent.state import Party
from src.scenarios import SCENARIOS, Scenario

SITUATION_PATH = Path(".local/lab-situation.json")


class LabSituation(BaseModel):
    id: str
    title: str
    party: str = "driver"
    tester_name: str = ""
    tester_brief: str = ""
    hidden: str = ""
    story: str
    agent_constraints: str
    expected_actions: list[str] = Field(default_factory=list)
    forbidden: list[str] = Field(default_factory=list)
    success_means: str
    opening_line: str = ""
    clock: str = ""
    shipment_id: str = ""
    origin: str = ""
    destination: str = ""
    vehicle_type: str = ""


def situation_path() -> Path:
    return Path(os.environ.get("MM_LAB_SITUATION", str(SITUATION_PATH)))


def from_scenario(scenario: Scenario, party: Party = Party.DRIVER) -> LabSituation:
    book = scenario.playbook(party)
    opening = scenario.openings.get(party, "")
    brief = "\n".join(
        [
            f"You are {book.you_are}.",
            f"Where: {book.where}",
            f"Opening posture: {book.opening_posture}",
            f"How to play: {book.how_to_play}",
        ]
    )
    return LabSituation(
        id=scenario.id,
        title=scenario.title,
        party=party.value,
        tester_brief=brief,
        hidden=book.hidden,
        story=scenario.story,
        agent_constraints=scenario.agent_constraints,
        expected_actions=list(scenario.expected_actions),
        forbidden=list(scenario.forbidden),
        success_means=scenario.success_means,
        opening_line=opening,
        clock=scenario.clock,
        shipment_id=scenario.shipment_id,
        origin=scenario.origin,
        destination=scenario.destination,
        vehicle_type=scenario.vehicle_type,
    )


def presets() -> list[LabSituation]:
    return [from_scenario(s) for s in SCENARIOS.values()]


def default_situation() -> LabSituation:
    from src.scenarios import BHIWANDI_GATE_HOLD

    return from_scenario(BHIWANDI_GATE_HOLD)


def save_situation(situation: LabSituation, path: Path | None = None) -> Path:
    target = path or situation_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(situation.model_dump_json(indent=2), encoding="utf-8")
    return target


def load_situation(path: Path | None = None) -> LabSituation:
    target = path or situation_path()
    if not target.exists():
        return default_situation()
    return LabSituation.model_validate_json(target.read_text(encoding="utf-8"))


def situation_from_mapping(data: object) -> LabSituation:
    if not isinstance(data, dict) or not data:
        return load_situation()
    preset_id = data.get("id")
    if preset_id in SCENARIOS and not data.get("story"):
        current = from_scenario(SCENARIOS[preset_id])
    else:
        current = load_situation()
    merged = current.model_dump()
    for key in LabSituation.model_fields:
        if key in data and data[key] not in (None,):
            merged[key] = data[key]
    return LabSituation.model_validate(merged)
