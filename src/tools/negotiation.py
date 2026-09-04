"""Write-path tools against shared session state."""

from __future__ import annotations

from typing import Any

from src.agent.coordinator import Coordinator
from src.agent.state import PartyOutcome


def update_negotiation_state(
    session_id: str,
    origin: str | None = None,
    destination: str | None = None,
    item_type: str | None = None,
    slot_date: str | None = None,
    offered_rate: float | None = None,
    accepted_rate: float | None = None,
    record_id: str | None = None,
    blocker: str | None = None,
    escalate: bool | None = None,
    vehicle_type: str | None = None,
    pickup_date: str | None = None,
    shipment_id: str | None = None,
) -> dict[str, Any]:
    """Patch the shared negotiation session."""
    coordinator = Coordinator()
    fields: dict[str, Any] = {
        "origin": origin,
        "destination": destination,
        "item_type": item_type or vehicle_type,
        "slot_date": slot_date or pickup_date,
        "offered_rate": offered_rate,
        "accepted_rate": accepted_rate,
        "record_id": record_id or shipment_id,
    }
    session = coordinator.update(session_id, **fields)
    if blocker:
        session.blockers.append(blocker)
        coordinator.store.put(session)
    if escalate:
        session.escalate_requested = True
        coordinator.store.put(session)
    return {"ok": True, "snapshot": session.snapshot()}


def end_party_call(
    session_id: str,
    outcome: str,
    summary: str,
    rate: float | None = None,
    blocker: str | None = None,
) -> dict[str, Any]:
    """Close the current party conversation and ask the coordinator what to do next."""
    try:
        parsed = PartyOutcome(outcome.strip().lower())
    except ValueError:
        parsed = PartyOutcome.BLOCKED
        blocker = blocker or f"unknown outcome: {outcome}"
    decision = Coordinator().record_party_end(
        session_id,
        outcome=parsed,
        summary=summary,
        rate=rate,
        blocker=blocker,
    )
    session = Coordinator().get(session_id)
    return {
        "ok": True,
        "decision": decision.model_dump(),
        "next_party": decision.party,
        "snapshot": session.snapshot(),
    }
