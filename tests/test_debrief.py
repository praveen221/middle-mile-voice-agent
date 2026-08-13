from src.agent.state import NegotiationSession, Party, PartyOutcome
from src.eval.debrief import debrief, format_debrief
from src.scenarios import get_scenario


def _session(**extra) -> NegotiationSession:
    return NegotiationSession(
        session_id="s1",
        scenario_id="same_day_appointment",
        current_party=Party.DRIVER,
        extra=extra,
    )


def test_auto_fail_without_tools():
    scenario = get_scenario()
    report = debrief(_session(), scenario)
    assert report["auto_pass"] is False
    assert report["checks"]["looked_up_rate_card"] is False


def test_auto_pass_when_closed_inside_cap():
    scenario = get_scenario()
    session = _session(tool_calls=["get_rate_card", "end_party_call"])
    session.accepted_rate = 23000
    session.party_outcomes["driver"] = PartyOutcome.ACCEPTED
    session.party_summaries["driver"] = "Driver agreed 23000, ETA 10:15."
    report = debrief(session, scenario)
    assert report["auto_pass"] is True
    assert report["checks"]["did_not_accept_over_max"] is True
    text = format_debrief(report)
    assert "AUTO PASS" in text
    assert "--party warehouse" in text


def test_accepting_over_max_fails():
    scenario = get_scenario()
    session = _session(tool_calls=["get_rate_card", "end_party_call"])
    session.accepted_rate = 28000
    session.party_outcomes["driver"] = PartyOutcome.ACCEPTED
    report = debrief(session, scenario)
    assert report["auto_pass"] is False
    assert report["checks"]["did_not_accept_over_max"] is False
