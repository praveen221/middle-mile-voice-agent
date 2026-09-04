from src.agent.state import Party
from src.scenarios import format_playbook, get_scenario


def test_default_case_is_the_sample_booking():
    scenario = get_scenario()
    assert scenario.record_id == "BK-1001"
    assert scenario.max_rate == 10000
    assert scenario.contracted_rate == 8000
    assert Party.VENDOR in scenario.playbooks
    assert "12,000" in scenario.playbooks[Party.VENDOR].opening_posture


def test_playbook_says_this_is_not_a_phone_call():
    text = format_playbook(get_scenario(), Party.VENDOR)
    assert "DOES NOT CALL YOUR PHONE" in text
    assert "Asha" in text
    assert "Andheri" in text


def test_unknown_scenario():
    try:
        get_scenario("nope")
    except KeyError:
        return
    raise AssertionError("expected KeyError")


def test_bootstrap_applies_scenario(isolated_store):
    from src.pipeline import bootstrap_session

    session = bootstrap_session(
        "t1",
        scenario_id="sample_price_hold",
        party="vendor",
    )
    assert session.scenario_id == "sample_price_hold"
    assert session.origin == "ANDHERI"
    assert session.destination == "BANDRA"
    assert session.current_party is Party.VENDOR
