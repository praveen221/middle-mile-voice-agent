"""Optional imported-call seed so the Lab DB is never empty on first run."""

from __future__ import annotations

from src.eval.db import CallDB

SEED_NOTE = "seed:sample-imported-call"


def seed_kimi_baseline(db: CallDB | None = None) -> int | None:
    db = db or CallDB()
    if db.has_notes(SEED_NOTE):
        return None
    call_id = db.start_call(
        session_id="local-eval",
        party="vendor",
        scenario_id="sample_price_hold",
        llm_provider="openrouter",
        llm_model="moonshotai/kimi-k2.5",
        stt="sarvam",
        tts="sarvam",
        prompt="Sample booking-desk brief (see src/agent/prompts.py).",
        snapshot='{"offered_rate": 10000, "accepted_rate": null, "blockers": ["Vendor demands 12000, max 10000"], "tools": ["lookup_price", "update_negotiation_state"]}',
        notes=SEED_NOTE,
        started_at="2026-08-14T08:30:00+00:00",
    )
    db.add_utterance(call_id, "note", "Imported placeholder so the Lab has one historical row.")
    db.add_tool(
        call_id,
        "lookup_price",
        {"origin": "ANDHERI", "destination": "BANDRA", "item_type": "half-day"},
        {"found": True, "max": 10000},
    )
    db.add_tool(call_id, "update_negotiation_state", {"offered_rate": 10000}, {"ok": True})
    db.end_call(call_id, status="imported")
    return call_id
