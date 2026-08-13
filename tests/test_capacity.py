from src.tools.capacity import check_capacity


def test_open_slot():
    result = check_capacity("BLR", "2026-08-14")
    assert result["found"] is True
    assert result["available"] is True
    assert result["slots"] == 3
    assert result["gate_out_latest"] == "12:00"
    assert result["reserved_window"] == "10:30-11:30"


def test_full_hub_points_to_next_date():
    result = check_capacity("Hyderabad", "2026-08-14")
    assert result["available"] is False
    assert result["next_available"] == "2026-08-15"


def test_tomorrow_alias():
    result = check_capacity("BLR", "tomorrow")
    assert result["date"] == "2026-08-14"
    assert result["found"] is True
