from src.tools.rate_card import get_rate_card, normalize_city, normalize_vehicle


def test_known_lane_aliases():
    card = get_rate_card("Bangalore", "Hyderabad", "19ft")
    assert card["found"] is True
    assert card["origin"] == "BLR"
    assert card["destination"] == "HYD"
    assert card["typical"] == 21000
    assert card["min"] < card["typical"] < card["max"]


def test_missing_lane():
    card = get_rate_card("Goa", "Kochi", "14ft")
    assert card["found"] is False
    assert "human" in card["message"].lower()


def test_normalizers():
    assert normalize_city("bengaluru") == "BLR"
    assert normalize_city("whitefield") == "BLR"
    assert normalize_city("patancheru") == "HYD"
    assert normalize_vehicle("Tata 407") == "407"


def test_bhiwandi_ahmedabad_32ft():
    row = get_rate_card("bhiwandi", "sanand", "32ft")
    assert row["found"] is True
    assert row["origin"] == "MUM"
    assert row["destination"] == "AMD"
    assert row["typical"] == 18500
    assert row["max"] == 22000
