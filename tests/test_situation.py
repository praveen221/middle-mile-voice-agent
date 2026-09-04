from src.agent.prompts import build_system_prompt
from src.agent.state import NegotiationSession, Party
from src.lab.situation import from_scenario, save_situation
from src.scenarios import SAMPLE_SLOT_GONE, get_scenario
from src.tools.rate_card import lookup_price
from src.tools.status import get_record_status


def test_slot_gone_case_is_registered():
    scenario = get_scenario("sample_slot_gone")
    assert scenario.record_id == "BK-1002"
    assert scenario.max_rate == 11000
    assert "released" in scenario.story.lower()
    assert scenario.forbidden
    assert scenario.expected_actions


def test_slot_gone_tools_exist():
    record = get_record_status("BK-1002")
    assert record["found"] is True
    assert record["origin"] == "POWAI"
    assert record["destination"] == "WORLI"
    rates = lookup_price("Powai", "Worli", "half-day")
    assert rates["found"] is True
    assert rates["max"] == 11000


def test_prompt_includes_situation_and_hides_tester_notes():
    situation = from_scenario(SAMPLE_SLOT_GONE)
    situation.tester_name = "Priya"
    session = NegotiationSession(session_id="s1", current_party=Party.VENDOR, scenario_id=situation.id)
    prompt = build_system_prompt(session, situation)
    assert "Powai" in prompt
    assert "Forbidden:" in prompt
    assert "Inventing a walk-in fee" in prompt
    assert situation.tester_brief
    assert situation.tester_brief not in prompt
    assert "Walk-away" not in prompt
    assert "98201" not in prompt
    assert "Priya" not in prompt


def test_saved_situation_roundtrip(tmp_path, monkeypatch):
    path = tmp_path / "sit.json"
    monkeypatch.setenv("MM_LAB_SITUATION", str(path))
    situation = from_scenario(SAMPLE_SLOT_GONE)
    situation.tester_name = "Asha"
    situation.story = "Edited story for this session."
    save_situation(situation, path)
    from src.lab.situation import load_situation

    loaded = load_situation(path)
    assert loaded.tester_name == "Asha"
    assert loaded.story == "Edited story for this session."
    assert loaded.id == "sample_slot_gone"
