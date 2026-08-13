"""Thin party-facing agent. The coordinator owns sequencing."""

from __future__ import annotations

from src.agent.prompts import PARTY_GOALS, build_system_prompt, opening_line
from src.agent.state import NegotiationSession, Party


class BaseAgent:
    def __init__(self, party: Party) -> None:
        self.party = party

    def goal(self) -> str:
        return PARTY_GOALS[self.party]

    def system_prompt(self, session: NegotiationSession) -> str:
        return build_system_prompt(session)

    def opening(self, session: NegotiationSession) -> str:
        return opening_line(self.party, session)
