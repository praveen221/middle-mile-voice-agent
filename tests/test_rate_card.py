from src.tools.rate_card import lookup_price, normalize_item, normalize_place


def test_known_pair_aliases():
    card = lookup_price("Andheri", "Bandra", "half-day")
    assert card["found"] is True
    assert card["origin"] == "ANDHERI"
    assert card["destination"] == "BANDRA"
    assert card["typical"] == 8000
    assert card["min"] < card["typical"] < card["max"]


def test_missing_pair():
    card = lookup_price("Goa", "Kochi", "hourly")
    assert card["found"] is False
    assert "human" in card["message"].lower()


def test_normalizers():
    assert normalize_place("lightroom") == "ANDHERI"
    assert normalize_place("studio") == "ANDHERI"
    assert normalize_item("half day") == "half-day"


def test_powai_worli_half_day():
    row = lookup_price("powai", "worli", "half-day")
    assert row["found"] is True
    assert row["origin"] == "POWAI"
    assert row["destination"] == "WORLI"
    assert row["typical"] == 9000
    assert row["max"] == 11000
