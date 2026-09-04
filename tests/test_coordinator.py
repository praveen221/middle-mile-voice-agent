from src.agent.coordinator import Coordinator, NextAction
from src.agent.state import Party, PartyOutcome


def _session(store) -> Coordinator:
    coordinator = Coordinator(store=store)
    coordinator.start(
        "s1",
        record_id="BK-1001",
        origin="ANDHERI",
        destination="BANDRA",
        item_type="half-day",
        slot_date="2026-08-14",
    )
    return coordinator


def test_happy_path_vendor_then_venue_then_client(isolated_store):
    c = _session(isolated_store)
    first = c.record_party_end("s1", outcome=PartyOutcome.ACCEPTED, summary="vendor ok", rate=9000)
    assert first.action == NextAction.CALL_NEXT
    assert first.party == Party.VENUE
    assert c.get("s1").accepted_rate == 9000

    second = c.record_party_end("s1", outcome=PartyOutcome.ACCEPTED, summary="slot ok")
    assert second.action == NextAction.CALL_NEXT
    assert second.party == Party.CLIENT

    done = c.record_party_end("s1", outcome=PartyOutcome.ACCEPTED, summary="client ok")
    assert done.action == NextAction.COMPLETE
    assert c.get("s1").status == "complete"


def test_venue_block_reopens_vendor(isolated_store):
    c = _session(isolated_store)
    c.record_party_end("s1", outcome=PartyOutcome.ACCEPTED, summary="vendor ok", rate=9000)
    back = c.record_party_end(
        "s1",
        outcome=PartyOutcome.BLOCKED,
        summary="no slot",
        blocker="Powai full on 14th",
    )
    assert back.action == NextAction.CALL_PREVIOUS
    assert back.party == Party.VENDOR
    assert c.get("s1").current_party == Party.VENDOR
    assert "Powai full on 14th" in c.get("s1").blockers


def test_vendor_reject_escalates(isolated_store):
    c = _session(isolated_store)
    decision = c.record_party_end(
        "s1",
        outcome=PartyOutcome.REJECTED,
        summary="wants 50k",
        blocker="rate too high",
    )
    assert decision.action == NextAction.ESCALATE
    assert c.get("s1").status == "escalated"


def test_handoff_cap_escalates(isolated_store):
    c = _session(isolated_store)
    c.max_handoffs = 1
    c.record_party_end("s1", outcome=PartyOutcome.ACCEPTED, summary="vendor ok", rate=9000)
    decision = c.record_party_end("s1", outcome=PartyOutcome.BLOCKED, summary="no slot")
    assert decision.action == NextAction.ESCALATE
