from src.agent.prompts import build_system_prompt
from src.agent.state import NegotiationSession, Party
from src.lab.situation import from_scenario, save_situation
from src.scenarios import BHIWANDI_GATE_HOLD, get_scenario
from src.tools.rate_card import get_rate_card
from src.tools.status import get_shipment_status


def test_bhiwandi_case_is_registered():
    scenario = get_scenario("bhiwandi_gate_hold")
    assert scenario.shipment_id == "MM-2044"
    assert scenario.max_rate == 22000
    assert "detention" in scenario.story.lower()
    assert scenario.forbidden
    assert scenario.expected_actions


def test_bhiwandi_tools_exist():
    ship = get_shipment_status("MM-2044")
    assert ship["found"] is True
    assert ship["origin"] == "MUM"
    assert ship["destination"] == "AMD"
    rates = get_rate_card("Bhiwandi", "Ahmedabad", "32ft")
    assert rates["found"] is True
    assert rates["max"] == 22000


def test_prompt_includes_situation_and_hides_tester_notes():
    situation = from_scenario(BHIWANDI_GATE_HOLD)
    situation.tester_name = "Priya"
    session = NegotiationSession(session_id="s1", current_party=Party.DRIVER, scenario_id=situation.id)
    prompt = build_system_prompt(session, situation)
    assert "Bhiwandi" in prompt
    assert "Forbidden:" in prompt
    assert "Inventing a detention" in prompt
    assert situation.tester_brief
    assert situation.tester_brief not in prompt
    assert "Walk-away" not in prompt
    assert "98201" not in prompt
    assert "Priya" not in prompt


def test_saved_situation_roundtrip(tmp_path, monkeypatch):
    path = tmp_path / "sit.json"
    monkeypatch.setenv("MM_LAB_SITUATION", str(path))
    situation = from_scenario(BHIWANDI_GATE_HOLD)
    situation.tester_name = "Asha"
    situation.story = "Edited story for this session."
    save_situation(situation, path)
    from src.lab.situation import load_situation

    loaded = load_situation(path)
    assert loaded.tester_name == "Asha"
    assert loaded.story == "Edited story for this session."
    assert loaded.id == "bhiwandi_gate_hold"
