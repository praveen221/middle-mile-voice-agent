"""Shared negotiation memory, keyed by session_id."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Protocol

from pydantic import BaseModel, Field


class Party(StrEnum):
    DRIVER = "driver"
    WAREHOUSE = "warehouse"
    CUSTOMER = "customer"
    HUMAN = "human"


class PartyOutcome(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    BLOCKED = "blocked"
    NO_ANSWER = "no_answer"


class NegotiationSession(BaseModel):
    session_id: str
    scenario_id: str | None = None
    goal: str = "Confirm vehicle, rate, warehouse slot, and customer delivery window."
    shipment_id: str | None = None
    origin: str | None = None
    destination: str | None = None
    vehicle_type: str | None = None
    pickup_date: str | None = None

    current_party: Party = Party.DRIVER
    party_order: list[Party] = Field(
        default_factory=lambda: [Party.DRIVER, Party.WAREHOUSE, Party.CUSTOMER]
    )
    party_outcomes: dict[str, PartyOutcome] = Field(default_factory=dict)
    party_summaries: dict[str, str] = Field(default_factory=dict)
    transcripts: dict[str, list[str]] = Field(default_factory=dict)

    offered_rate: float | None = None
    accepted_rate: float | None = None
    currency: str = "INR"
    blockers: list[str] = Field(default_factory=list)

    escalate_requested: bool = False
    handoff_count: int = 0
    turn_count: int = 0
    status: str = "open"
    extra: dict[str, Any] = Field(default_factory=dict)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def note(self, party: Party, line: str) -> None:
        self.transcripts.setdefault(party.value, []).append(line)
        self.updated_at = datetime.now(UTC)

    def snapshot(self) -> str:
        """Compact state the LLM can hear as context."""
        parts = [
            f"goal: {self.goal}",
            f"shipment: {self.shipment_id or 'unknown'}",
            f"lane: {self.origin or '?'} -> {self.destination or '?'}",
            f"vehicle: {self.vehicle_type or 'unknown'}",
            f"pickup_date: {self.pickup_date or 'unknown'}",
            f"offered_rate: {self.offered_rate}",
            f"accepted_rate: {self.accepted_rate}",
            f"current_party: {self.current_party}",
            f"outcomes: {self.party_outcomes}",
            f"blockers: {self.blockers}",
            f"handoffs: {self.handoff_count}",
        ]
        return " | ".join(parts)


class SessionStore(Protocol):
    def get(self, session_id: str) -> NegotiationSession | None: ...
    def put(self, session: NegotiationSession) -> None: ...
    def delete(self, session_id: str) -> None: ...
    def all(self) -> list[NegotiationSession]: ...


class InMemorySessionStore:
    def __init__(self) -> None:
        self._data: dict[str, NegotiationSession] = {}

    def get(self, session_id: str) -> NegotiationSession | None:
        return self._data.get(session_id)

    def put(self, session: NegotiationSession) -> None:
        session.updated_at = datetime.now(UTC)
        self._data[session.session_id] = session

    def delete(self, session_id: str) -> None:
        self._data.pop(session_id, None)

    def all(self) -> list[NegotiationSession]:
        return list(self._data.values())


class RedisSessionStore:
    """Optional Redis backend. Import redis only when this class is used."""

    PREFIX = "mm:session:"

    def __init__(self, url: str) -> None:
        import redis

        self._r = redis.Redis.from_url(url, decode_responses=True)

    def get(self, session_id: str) -> NegotiationSession | None:
        raw = self._r.get(f"{self.PREFIX}{session_id}")
        if not raw:
            return None
        return NegotiationSession.model_validate_json(raw)

    def put(self, session: NegotiationSession) -> None:
        session.updated_at = datetime.now(UTC)
        self._r.set(f"{self.PREFIX}{session.session_id}", session.model_dump_json())

    def delete(self, session_id: str) -> None:
        self._r.delete(f"{self.PREFIX}{session_id}")

    def all(self) -> list[NegotiationSession]:
        keys = list(self._r.scan_iter(f"{self.PREFIX}*"))
        out: list[NegotiationSession] = []
        for key in keys:
            raw = self._r.get(key)
            if raw:
                out.append(NegotiationSession.model_validate_json(raw))
        return out


_STORE: SessionStore | None = None


def get_store(redis_url: str = "") -> SessionStore:
    global _STORE
    if _STORE is None:
        _STORE = RedisSessionStore(redis_url) if redis_url else InMemorySessionStore()
    return _STORE


def reset_store() -> None:
    global _STORE
    _STORE = None


def session_to_dict(session: NegotiationSession) -> dict[str, Any]:
    return json.loads(session.model_dump_json())
