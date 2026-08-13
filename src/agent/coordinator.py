"""Multi-party brain: who to talk to next, and when to stop."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel

from src.agent.state import (
    NegotiationSession,
    Party,
    PartyOutcome,
    SessionStore,
    get_store,
)
from src.config import get_settings


class NextAction(StrEnum):
    CONTINUE = "continue"
    CALL_NEXT = "call_next"
    CALL_PREVIOUS = "call_previous"
    ESCALATE = "escalate"
    COMPLETE = "complete"
    HANGUP = "hangup"


class Decision(BaseModel):
    action: NextAction
    party: Party | None = None
    reason: str
    hangup_current: bool = True


class Coordinator:
    def __init__(self, store: SessionStore | None = None) -> None:
        self.store = store or get_store(get_settings().redis_url)
        settings = get_settings()
        self.max_handoffs = settings.max_handoffs
        self.max_party_turns = settings.max_party_turns

    def start(
        self,
        session_id: str,
        *,
        goal: str | None = None,
        shipment_id: str | None = None,
        origin: str | None = None,
        destination: str | None = None,
        vehicle_type: str | None = None,
        pickup_date: str | None = None,
        first_party: Party = Party.DRIVER,
    ) -> NegotiationSession:
        existing = self.store.get(session_id)
        if existing:
            return existing
        session = NegotiationSession(
            session_id=session_id,
            goal=goal or NegotiationSession.model_fields["goal"].default,
            shipment_id=shipment_id,
            origin=origin,
            destination=destination,
            vehicle_type=vehicle_type,
            pickup_date=pickup_date,
            current_party=first_party,
            party_outcomes={p.value: PartyOutcome.PENDING for p in [first_party]},
        )
        self.store.put(session)
        return session

    def get(self, session_id: str) -> NegotiationSession:
        session = self.store.get(session_id)
        if session is None:
            raise KeyError(f"unknown session {session_id}")
        return session

    def update(self, session_id: str, **fields: object) -> NegotiationSession:
        session = self.get(session_id)
        allowed = set(NegotiationSession.model_fields)
        for key, value in fields.items():
            if key not in allowed or value is None:
                continue
            setattr(session, key, value)
        session.turn_count += 1
        self.store.put(session)
        return session

    def record_party_end(
        self,
        session_id: str,
        *,
        outcome: PartyOutcome,
        summary: str,
        rate: float | None = None,
        blocker: str | None = None,
    ) -> Decision:
        session = self.get(session_id)
        party = session.current_party
        session.party_outcomes[party.value] = outcome
        session.party_summaries[party.value] = summary
        if rate is not None:
            if outcome == PartyOutcome.ACCEPTED:
                session.accepted_rate = rate
            else:
                session.offered_rate = rate
        if blocker:
            session.blockers.append(blocker)
        if outcome == PartyOutcome.BLOCKED:
            session.escalate_requested = session.escalate_requested or False
        decision = self.decide(session)
        if decision.action == NextAction.CALL_NEXT and decision.party:
            session.current_party = decision.party
            session.handoff_count += 1
            session.party_outcomes.setdefault(decision.party.value, PartyOutcome.PENDING)
        elif decision.action == NextAction.CALL_PREVIOUS and decision.party:
            session.current_party = decision.party
            session.handoff_count += 1
            session.party_outcomes[decision.party.value] = PartyOutcome.PENDING
        elif decision.action == NextAction.ESCALATE:
            session.current_party = Party.HUMAN
            session.status = "escalated"
        elif decision.action == NextAction.COMPLETE:
            session.status = "complete"
        elif decision.action == NextAction.HANGUP:
            session.status = "closed"
        self.store.put(session)
        return decision

    def decide(self, session: NegotiationSession) -> Decision:
        if session.escalate_requested:
            return Decision(
                action=NextAction.ESCALATE,
                party=Party.HUMAN,
                reason="Human escalate flag is set.",
            )
        if session.handoff_count >= self.max_handoffs:
            return Decision(
                action=NextAction.ESCALATE,
                party=Party.HUMAN,
                reason=f"Handoff cap {self.max_handoffs} reached.",
            )
        if session.turn_count >= self.max_party_turns * max(len(session.party_order), 1):
            return Decision(
                action=NextAction.ESCALATE,
                party=Party.HUMAN,
                reason="Turn budget exhausted.",
            )

        current = session.current_party
        current_outcome = session.party_outcomes.get(current.value, PartyOutcome.PENDING)

        if current_outcome == PartyOutcome.PENDING:
            return Decision(
                action=NextAction.CONTINUE,
                party=current,
                reason="Current party conversation is still open.",
                hangup_current=False,
            )

        if current_outcome == PartyOutcome.NO_ANSWER:
            nxt = self._next_party(session, current)
            if nxt:
                return Decision(
                    action=NextAction.CALL_NEXT,
                    party=nxt,
                    reason=f"{current} did not answer; trying {nxt}.",
                )
            return Decision(action=NextAction.HANGUP, reason="No answer and no next party.")

        if current_outcome in {PartyOutcome.REJECTED, PartyOutcome.BLOCKED}:
            prev = self._previous_party(session, current)
            if prev:
                return Decision(
                    action=NextAction.CALL_PREVIOUS,
                    party=prev,
                    reason=f"{current} {current_outcome}; reopening {prev} with the new constraint.",
                )
            return Decision(
                action=NextAction.ESCALATE,
                party=Party.HUMAN,
                reason=f"{current} {current_outcome} and there is no previous party to reopen.",
            )

        if self._all_required_accepted(session):
            return Decision(
                action=NextAction.COMPLETE,
                reason="Driver, warehouse, and customer have accepted.",
            )

        nxt = self._next_unresolved(session)
        if nxt:
            return Decision(
                action=NextAction.CALL_NEXT,
                party=nxt,
                reason=f"{current} accepted; calling {nxt}.",
            )
        return Decision(action=NextAction.HANGUP, reason="No remaining parties.")

    def _all_required_accepted(self, session: NegotiationSession) -> bool:
        required = [p.value for p in session.party_order]
        return all(session.party_outcomes.get(p) == PartyOutcome.ACCEPTED for p in required)

    def _next_party(self, session: NegotiationSession, current: Party) -> Party | None:
        order = session.party_order
        if current not in order:
            return order[0] if order else None
        idx = order.index(current)
        if idx + 1 < len(order):
            return order[idx + 1]
        return None

    def _previous_party(self, session: NegotiationSession, current: Party) -> Party | None:
        order = session.party_order
        if current not in order:
            return None
        idx = order.index(current)
        if idx > 0:
            return order[idx - 1]
        return None

    def _next_unresolved(self, session: NegotiationSession) -> Party | None:
        for party in session.party_order:
            outcome = session.party_outcomes.get(party.value)
            if outcome in {None, PartyOutcome.PENDING}:
                return party
        return None


def default_coordinator() -> Coordinator:
    return Coordinator()
