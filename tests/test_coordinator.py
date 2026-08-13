from src.agent.coordinator import Coordinator, NextAction
from src.agent.state import Party, PartyOutcome


def _session(store) -> Coordinator:
    coordinator = Coordinator(store=store)
    coordinator.start(
        "s1",
        shipment_id="MM-1001",
        origin="BLR",
        destination="HYD",
        vehicle_type="19ft",
        pickup_date="2026-08-14",
    )
    return coordinator


def test_happy_path_driver_then_warehouse_then_customer(isolated_store):
    c = _session(isolated_store)
    first = c.record_party_end("s1", outcome=PartyOutcome.ACCEPTED, summary="driver ok", rate=21000)
    assert first.action == NextAction.CALL_NEXT
    assert first.party == Party.WAREHOUSE
    assert c.get("s1").accepted_rate == 21000

    second = c.record_party_end("s1", outcome=PartyOutcome.ACCEPTED, summary="slot ok")
    assert second.action == NextAction.CALL_NEXT
    assert second.party == Party.CUSTOMER

    done = c.record_party_end("s1", outcome=PartyOutcome.ACCEPTED, summary="customer ok")
    assert done.action == NextAction.COMPLETE
    assert c.get("s1").status == "complete"


def test_warehouse_block_reopens_driver(isolated_store):
    c = _session(isolated_store)
    c.record_party_end("s1", outcome=PartyOutcome.ACCEPTED, summary="driver ok", rate=21000)
    back = c.record_party_end(
        "s1",
        outcome=PartyOutcome.BLOCKED,
        summary="no slot",
        blocker="HYD full on 14th",
    )
    assert back.action == NextAction.CALL_PREVIOUS
    assert back.party == Party.DRIVER
    assert c.get("s1").current_party == Party.DRIVER
    assert "HYD full on 14th" in c.get("s1").blockers


def test_driver_reject_escalates(isolated_store):
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
    c.record_party_end("s1", outcome=PartyOutcome.ACCEPTED, summary="driver ok", rate=21000)
    # warehouse blocks → would reopen driver, but handoff_count is already 1
    decision = c.record_party_end("s1", outcome=PartyOutcome.BLOCKED, summary="no slot")
    assert decision.action == NextAction.ESCALATE
