"""Score what the agent actually did. Language still needs a human ear."""

from __future__ import annotations

from src.agent.state import NegotiationSession, Party, PartyOutcome
from src.scenarios.types import Scenario


def debrief(session: NegotiationSession, scenario: Scenario) -> dict:
    tools = list(session.extra.get("tool_calls") or [])
    rate = session.accepted_rate if session.accepted_rate is not None else session.offered_rate
    party = session.current_party.value
    closed_parties = [
        name
        for name, outcome in session.party_outcomes.items()
        if outcome != PartyOutcome.PENDING
    ]
    accepted_over_max = (
        session.accepted_rate is not None and session.accepted_rate > scenario.max_rate
    )
    checks = {
        "looked_up_price": "lookup_price" in tools or "get_rate_card" in tools,
        "looked_up_record": "get_record_status" in tools or "get_shipment_status" in tools,
        "wrote_state": "update_negotiation_state" in tools,
        "closed_the_party": "end_party_call" in tools or bool(closed_parties),
        "rate_within_cap_or_escalated": (not accepted_over_max)
        or session.status == "escalated",
        "did_not_accept_over_max": not accepted_over_max,
        "captured_a_number": rate is not None,
    }
    auto_pass = all(
        checks[k]
        for k in (
            "looked_up_price",
            "closed_the_party",
            "did_not_accept_over_max",
        )
    )
    return {
        "scenario": scenario.id,
        "title": scenario.title,
        "party_now": party,
        "status": session.status,
        "accepted_rate": session.accepted_rate,
        "offered_rate": session.offered_rate,
        "max_rate": scenario.max_rate,
        "outcomes": {k: (v.value if hasattr(v, "value") else v) for k, v in session.party_outcomes.items()},
        "summaries": session.party_summaries,
        "blockers": session.blockers,
        "tools": tools,
        "checks": checks,
        "auto_pass": auto_pass,
        "human_listen_for": [
            "Did it sound like a person or a chatbot?",
            "Did it quote a price before the tool returned?",
            "Did it dump a hidden penalty number?",
            "Did you have to repeat yourself more than once?",
            "Would a real person stay on this call?",
        ],
    }


def format_debrief(report: dict) -> str:
    checks = report["checks"]
    lines = [
        "",
        "=" * 64,
        "DEBRIEF",
        "=" * 64,
        f"{report['title']}   status={report['status']}",
        f"accepted={report['accepted_rate']}  offered={report['offered_rate']}  cap={report['max_rate']}",
        f"outcomes={report['outcomes']}",
        f"blockers={report['blockers']}",
        f"tools={report['tools']}",
        "",
        "AUTOMATIC CHECKS",
    ]
    for name, ok in checks.items():
        lines.append(f"  [{'ok' if ok else 'NO'}] {name}")
    lines.append("")
    lines.append("AUTO PASS" if report["auto_pass"] else "AUTO FAIL — see the NOs above")
    lines.append("")
    lines.append("YOU STILL HAVE TO SCORE BY EAR")
    for item in report["human_listen_for"]:
        lines.append(f"  - {item}")
    if report["summaries"]:
        lines.append("")
        lines.append("AGENT SUMMARIES")
        for party, text in report["summaries"].items():
            lines.append(f"  {party}: {text}")
    next_party = None
    outcomes = report["outcomes"]
    for name in (p.value for p in (Party.VENDOR, Party.VENUE, Party.CLIENT)):
        if outcomes.get(name) in {None, "pending"}:
            next_party = name
            break
    if report["status"] == "escalated":
        lines.append("Session escalated. Read the blocker, then start over with --fresh.")
    elif next_party:
        lines.append(
            f"Next leg (same terminal): python scripts/run_local.py --party {next_party}"
        )
    else:
        lines.append("All three parties have an outcome. Start over with --fresh if you want.")
    lines.append("=" * 64)
    lines.append("")
    return "\n".join(lines)
