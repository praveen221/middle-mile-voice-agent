from src.eval.db import CallDB
from src.eval.seed import seed_kimi_baseline


def test_records_and_summarizes(tmp_path):
    db = CallDB(tmp_path / "calls.db")
    call_id = db.start_call(
        session_id="s",
        party="driver",
        scenario_id="same_day_appointment",
        llm_provider="sarvam",
        llm_model="sarvam-105b",
        stt="sarvam",
        tts="sarvam",
        prompt="hello",
    )
    db.add_utterance(call_id, "user", "28 hazaar chahiye")
    db.add_utterance(call_id, "assistant", "24 se upar nahi ho payega")
    db.add_tool(call_id, "get_rate_card", {"origin": "BLR"}, {"max": 24000})
    db.add_metric(call_id, kind="llm_tokens", prompt_tokens=10, completion_tokens=5, total_tokens=15)
    db.end_call(call_id, status="open")
    summary = db.call_summary(call_id)
    assert summary["tokens"]["total"] == 15
    assert len(summary["utterances"]) == 2
    assert summary["tools"][0]["name"] == "get_rate_card"


def test_stores_situation_and_transcript(tmp_path):
    db = CallDB(tmp_path / "calls.db")
    call_id = db.start_call(
        session_id="s",
        party="driver",
        scenario_id="bhiwandi_gate_hold",
        llm_provider="openrouter",
        llm_model="qwen",
        stt="sarvam",
        tts="sarvam",
        prompt="FULL PROMPT TEXT",
        situation_title="Bhiwandi gate hold — detention + e-way mismatch",
        situation_json='{"id":"bhiwandi_gate_hold"}',
        tester_name="Asha",
    )
    db.add_utterance(call_id, "user", "teen hazaar detention do", source="stt", finalized=True)
    db.add_utterance(call_id, "assistant", "detention card pe nahi hai", source="llm", finalized=True)
    db.end_call(call_id, status="escalated")
    row = db.call_summary(call_id)["call"]
    assert row["situation_title"].startswith("Bhiwandi")
    assert row["tester_name"] == "Asha"
    assert row["prompt"] == "FULL PROMPT TEXT"
    assert "USER: teen hazaar detention do" in row["transcript"]
    assert "AGENT: detention card pe nahi hai" in row["transcript"]


def test_stt_utterance_collapses_partials(tmp_path):
    db = CallDB(tmp_path / "calls.db")
    call_id = db.start_call(
        session_id="s",
        party="driver",
        scenario_id="same_day_appointment",
        llm_provider="openrouter",
        llm_model="qwen",
        stt="sarvam",
        tts="sarvam",
        prompt="p",
    )
    db.add_utterance(call_id, "user", "28", source="stt", finalized=False)
    db.add_utterance(call_id, "user", "28 hazaar", source="stt", finalized=False)
    db.add_utterance(call_id, "user", "28 hazaar chahiye", source="stt", finalized=True)
    rows = db.call_summary(call_id)["utterances"]
    assert len(rows) == 1
    assert rows[0]["text"] == "28 hazaar chahiye"


def test_apply_reuses_config_and_groups_calls(tmp_path):
    db = CallDB(tmp_path / "calls.db")
    stack = {"stt": "sarvam", "stt_language": "hi", "tts": "sarvam", "tts_language": "hi", "tts_voice": "shubh", "llm_provider": "openrouter", "llm_model": "qwen"}
    situation = {"id": "bhiwandi_gate_hold", "title": "Bhiwandi", "story": "s", "agent_constraints": "c", "success_means": "ok", "tester_name": "Asha"}
    first = db.save_config(stack=stack, situation=situation)
    second = db.save_config(stack=stack, situation={**situation, "tester_name": "Priya"})
    assert first["id"] == second["id"]
    assert second["reused"] is True
    changed = db.save_config(stack=stack, situation={**situation, "story": "edited"})
    assert changed["id"] != first["id"]
    a = db.start_call(session_id="1", party="driver", scenario_id="bhiwandi_gate_hold", llm_provider="openrouter", llm_model="qwen", stt="sarvam", tts="sarvam", prompt="p", config_id=first["id"], tester_name="Asha")
    b = db.start_call(session_id="2", party="driver", scenario_id="bhiwandi_gate_hold", llm_provider="openrouter", llm_model="qwen", stt="sarvam", tts="sarvam", prompt="p", config_id=first["id"], tester_name="Priya")
    db.start_call(session_id="3", party="driver", scenario_id="bhiwandi_gate_hold", llm_provider="openrouter", llm_model="qwen", stt="sarvam", tts="sarvam", prompt="p", config_id=changed["id"])
    grouped = db.list_calls(config_id=first["id"])
    assert {row["id"] for row in grouped} == {a, b}
    assert db.active_config_id() == changed["id"]


def test_seed_is_idempotent(tmp_path):
    db = CallDB(tmp_path / "calls.db")
    first = seed_kimi_baseline(db)
    second = seed_kimi_baseline(db)
    assert first is not None
    assert second is None
    summary = db.call_summary(first)
    assert summary["tokens"]["total"] == 21298
