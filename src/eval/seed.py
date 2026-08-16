"""Seed the Kimi baseline call you already ran."""

from __future__ import annotations

from src.eval.db import CallDB

SEED_NOTE = "seed:kimi-k2.5-2026-08-14-playground"


def seed_kimi_baseline(db: CallDB | None = None) -> int | None:
    db = db or CallDB()
    if db.has_notes(SEED_NOTE):
        return None
    call_id = db.start_call(
        session_id="local-eval",
        party="driver",
        scenario_id="same_day_appointment",
        llm_provider="openrouter",
        llm_model="moonshotai/kimi-k2.5",
        stt="sarvam",
        tts="sarvam",
        prompt="Same-day Whitefield → Patancheru desk brief (see src/agent/prompts.py).",
        snapshot='{"offered_rate": 24000, "accepted_rate": null, "blockers": ["Driver demands 28000, max 24000"], "tools": ["get_rate_card", "update_negotiation_state"]}',
        notes=SEED_NOTE,
        started_at="2026-08-14T08:30:00+00:00",
    )
    db.add_utterance(call_id, "note", "Imported from Pipecat playground Metrics tab. No live transcript was saved.")
    db.add_tool(call_id, "get_rate_card", {"origin": "BLR", "destination": "HYD", "vehicle_type": "19ft"}, {"found": True, "max": 24000})
    db.add_tool(call_id, "update_negotiation_state", {"offered_rate": 24000}, {"ok": True})
    db.add_metric(
        call_id,
        kind="llm_tokens",
        processor="OpenRouterLLMService#0",
        model="moonshotai/kimi-k2.5",
        prompt_tokens=19469,
        completion_tokens=1829,
        total_tokens=21298,
        extra={"source": "playground Metrics tab", "est_cost_usd": 0.011},
    )
    # Representative TTFB points from the charts (ms).
    for ms in (0, 400, 1200, 500, 780, 980, 500, 500, 750):
        db.add_metric(call_id, kind="ttfb", processor="SarvamSTTService#0", model="saaras:v3", ttfb_ms=ms)
    for ms in (0, 2300, 1500, 2000, 0, 2950, 1300, 1400, 1400, 1200, 1500, 2250, 1000, 2050, 1050):
        db.add_metric(call_id, kind="ttfb", processor="OpenRouterLLMService#0", model="moonshotai/kimi-k2.5", ttfb_ms=ms)
    for ms in (0, 230, 235, 250, 220, 230, 240, 10, 230, 220, 260):
        db.add_metric(call_id, kind="ttfb", processor="SarvamTTSService#0", model="bulbul:v3", ttfb_ms=ms)
    db.end_call(call_id, status="imported")
    return call_id
