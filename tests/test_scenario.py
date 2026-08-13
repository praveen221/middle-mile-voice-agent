from src.agent.state import Party
from src.scenarios import format_playbook, get_scenario


def test_default_case_is_the_same_day_load():
    scenario = get_scenario()
    assert scenario.shipment_id == "MM-1001"
    assert scenario.max_rate == 24000
    assert scenario.contracted_rate == 21000
    assert Party.DRIVER in scenario.playbooks
    assert "28,000" in scenario.playbooks[Party.DRIVER].opening_posture or "28000" in scenario.playbooks[Party.DRIVER].opening_posture.replace(",", "")


def test_playbook_says_this_is_not_a_phone_call():
    text = format_playbook(get_scenario(), Party.DRIVER)
    assert "DOES NOT CALL YOUR PHONE" in text
    assert "Ramesh" in text
    assert "Whitefield" in text


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
        scenario_id="same_day_appointment",
        party="driver",
    )
    assert session.scenario_id == "same_day_appointment"
    assert session.origin == "BLR"
    assert session.destination == "HYD"
    assert session.current_party is Party.DRIVER
