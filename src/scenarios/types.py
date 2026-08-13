"""Typed case file for a local eval run."""

from __future__ import annotations

from pydantic import BaseModel, Field

from src.agent.state import Party


class PartyPlaybook(BaseModel):
    you_are: str
    where: str
    opening_posture: str
    how_to_play: str
    hidden: str = ""


class Scenario(BaseModel):
    id: str
    title: str
    shipment_id: str
    origin: str
    destination: str
    vehicle_type: str
    pickup_date: str
    clock: str
    contracted_rate: float
    max_rate: float
    min_rate: float
    typical_rate: float
    miss_penalty: float
    story: str
    agent_constraints: str
    success_means: str
    what_this_tests: str
    playbooks: dict[Party, PartyPlaybook]
    openings: dict[Party, str] = Field(default_factory=dict)

    def playbook(self, party: Party) -> PartyPlaybook:
        return self.playbooks[party]
