from src.agent.state import NegotiationSession, Party, PartyOutcome
from src.eval.debrief import debrief, format_debrief
from src.scenarios import get_scenario


def _session(**extra) -> NegotiationSession:
    return NegotiationSession(
        session_id="s1",
        scenario_id="sample_price_hold",
        current_party=Party.VENDOR,
        extra=extra,
    )


def test_auto_fail_without_tools():
    scenario = get_scenario()
    report = debrief(_session(), scenario)
    assert report["auto_pass"] is False
    assert report["checks"]["looked_up_price"] is False


def test_auto_pass_when_closed_inside_cap():
    scenario = get_scenario()
    session = _session(tool_calls=["lookup_price", "end_party_call"])
    session.accepted_rate = 9000
    session.party_outcomes["vendor"] = PartyOutcome.ACCEPTED
    session.party_summaries["vendor"] = "Vendor agreed 9000, ETA 15:45."
    report = debrief(session, scenario)
    assert report["auto_pass"] is True
    assert report["checks"]["did_not_accept_over_max"] is True
    text = format_debrief(report)
    assert "AUTO PASS" in text
    assert "--party venue" in text


def test_accepting_over_max_fails():
    scenario = get_scenario()
    session = _session(tool_calls=["lookup_price", "end_party_call"])
    session.accepted_rate = 12000
    session.party_outcomes["vendor"] = PartyOutcome.ACCEPTED
    report = debrief(session, scenario)
    assert report["auto_pass"] is False
    assert report["checks"]["did_not_accept_over_max"] is False
