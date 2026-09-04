from src.tools.capacity import check_availability


def test_open_slot():
    result = check_availability("ANDHERI", "2026-08-14")
    assert result["found"] is True
    assert result["available"] is True
    assert result["slots"] == 2
    assert result["gate_out_latest"] == "15:30"
    assert result["reserved_window"] == "16:00-18:00"


def test_full_site_points_to_next_date():
    result = check_availability("Bandra", "2026-08-14")
    assert result["available"] is False
    assert result["next_available"] == "2026-08-15"


def test_tomorrow_alias():
    result = check_availability("ANDHERI", "tomorrow")
    assert result["date"] == "2026-08-14"
    assert result["found"] is True
