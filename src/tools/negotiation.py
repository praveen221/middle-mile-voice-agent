"""Write-path tools against shared session state."""

from __future__ import annotations

from typing import Any

from src.agent.coordinator import Coordinator
from src.agent.state import PartyOutcome


def update_negotiation_state(
    session_id: str,
    origin: str | None = None,
    destination: str | None = None,
    vehicle_type: str | None = None,
    pickup_date: str | None = None,
    offered_rate: float | None = None,
    accepted_rate: float | None = None,
    shipment_id: str | None = None,
    blocker: str | None = None,
    escalate: bool | None = None,
) -> dict[str, Any]:
    """Patch the shared negotiation session.

    Args:
        session_id: Active negotiation id.
        origin: Pickup city if newly known.
        destination: Drop city if newly known.
        vehicle_type: Vehicle if newly known.
        pickup_date: ISO date if newly known.
        offered_rate: Rate currently on the table.
        accepted_rate: Rate a party has agreed.
        shipment_id: Shipment id if newly known.
        blocker: Optional blocker to append.
        escalate: Set True to force a human handoff.
    """
    coordinator = Coordinator()
    fields: dict[str, Any] = {
        "origin": origin,
        "destination": destination,
        "vehicle_type": vehicle_type,
        "pickup_date": pickup_date,
        "offered_rate": offered_rate,
        "accepted_rate": accepted_rate,
        "shipment_id": shipment_id,
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
    """Close the current party conversation and ask the coordinator what to do next.

    Args:
        session_id: Active negotiation id.
        outcome: One of accepted, rejected, blocked, no_answer.
        summary: One spoken-language sentence of what happened.
        rate: Rate discussed, if any.
        blocker: Why it failed, if it failed.
    """
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
