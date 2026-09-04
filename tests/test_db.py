from src.eval.db import CallDB
from src.eval.seed import seed_kimi_baseline


def test_records_and_summarizes(tmp_path):
    db = CallDB(tmp_path / "calls.db")
    call_id = db.start_call(
        session_id="s",
        party="vendor",
        scenario_id="sample_price_hold",
        llm_provider="sarvam",
        llm_model="sarvam-105b",
        stt="sarvam",
        tts="sarvam",
        prompt="hello",
    )
    db.add_utterance(call_id, "user", "barah hazaar chahiye")
    db.add_utterance(call_id, "assistant", "das se upar nahi ho payega")
    db.add_tool(call_id, "lookup_price", {"origin": "ANDHERI"}, {"max": 10000})
    db.add_metric(call_id, kind="llm_tokens", prompt_tokens=10, completion_tokens=5, total_tokens=15)
    db.end_call(call_id, status="open")
    summary = db.call_summary(call_id)
    assert summary["tokens"]["total"] == 15
    assert len(summary["utterances"]) == 2
    assert summary["tools"][0]["name"] == "lookup_price"


def test_stores_situation_and_transcript(tmp_path):
    db = CallDB(tmp_path / "calls.db")
    call_id = db.start_call(
        session_id="s",
        party="vendor",
        scenario_id="sample_slot_gone",
        llm_provider="openrouter",
        llm_model="qwen",
        stt="sarvam",
        tts="sarvam",
        prompt="FULL PROMPT TEXT",
        situation_title="Sample: venue released the 4pm slot",
        situation_json='{"id":"sample_slot_gone"}',
        tester_name="Asha",
    )
    db.add_utterance(call_id, "user", "slot confirm hai na", source="stt", finalized=True)
    db.add_utterance(call_id, "assistant", "hold expire ho chuka hai", source="llm", finalized=True)
    db.end_call(call_id, status="escalated")
    row = db.call_summary(call_id)["call"]
    assert row["situation_title"].startswith("Sample:")
    assert row["tester_name"] == "Asha"
    assert row["prompt"] == "FULL PROMPT TEXT"
    assert "USER: slot confirm hai na" in row["transcript"]
    assert "AGENT: hold expire ho chuka hai" in row["transcript"]


def test_stt_utterance_collapses_partials(tmp_path):
    db = CallDB(tmp_path / "calls.db")
    call_id = db.start_call(
        session_id="s",
        party="vendor",
        scenario_id="sample_price_hold",
        llm_provider="openrouter",
        llm_model="qwen",
        stt="sarvam",
        tts="sarvam",
        prompt="p",
    )
    db.add_utterance(call_id, "user", "12", source="stt", finalized=False)
    db.add_utterance(call_id, "user", "12 hazaar", source="stt", finalized=False)
    db.add_utterance(call_id, "user", "12 hazaar chahiye", source="stt", finalized=True)
    rows = db.call_summary(call_id)["utterances"]
    assert len(rows) == 1
    assert rows[0]["text"] == "12 hazaar chahiye"


def test_apply_reuses_config_and_groups_calls(tmp_path):
    db = CallDB(tmp_path / "calls.db")
    stack = {"stt": "sarvam", "stt_language": "hi", "tts": "sarvam", "tts_language": "hi", "tts_voice": "shubh", "llm_provider": "openrouter", "llm_model": "qwen"}
    situation = {"id": "sample_slot_gone", "title": "Slot gone", "story": "s", "agent_constraints": "c", "success_means": "ok", "tester_name": "Asha"}
    first = db.save_config(stack=stack, situation=situation)
    second = db.save_config(stack=stack, situation={**situation, "tester_name": "Priya"})
    assert first["id"] == second["id"]
    assert second["reused"] is True
    changed = db.save_config(stack=stack, situation={**situation, "story": "edited"})
    assert changed["id"] != first["id"]
    a = db.start_call(session_id="1", party="vendor", scenario_id="sample_slot_gone", llm_provider="openrouter", llm_model="qwen", stt="sarvam", tts="sarvam", prompt="p", config_id=first["id"], tester_name="Asha")
    b = db.start_call(session_id="2", party="vendor", scenario_id="sample_slot_gone", llm_provider="openrouter", llm_model="qwen", stt="sarvam", tts="sarvam", prompt="p", config_id=first["id"], tester_name="Priya")
    db.start_call(session_id="3", party="vendor", scenario_id="sample_slot_gone", llm_provider="openrouter", llm_model="qwen", stt="sarvam", tts="sarvam", prompt="p", config_id=changed["id"])
    grouped = db.list_calls(config_id=first["id"])
    assert {row["id"] for row in grouped} == {a, b}
    assert db.active_config_id() == changed["id"]


def test_seed_is_idempotent(tmp_path):
    db = CallDB(tmp_path / "calls.db")
    first = seed_kimi_baseline(db)
    second = seed_kimi_baseline(db)
    assert first is not None
    assert second is None
