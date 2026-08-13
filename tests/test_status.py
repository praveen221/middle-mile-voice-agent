from src.tools.status import get_shipment_status


def test_known_shipment():
    row = get_shipment_status("mm-1001")
    assert row["found"] is True
    assert row["origin"] == "BLR"
    assert row["destination"] == "HYD"
    assert row["driver_phone"].startswith("+91")
    assert row["driver_name"] == "Ramesh"
    assert row["gate_out_latest"] == "12:00"


def test_missing_shipment():
    row = get_shipment_status("NOPE")
    assert row["found"] is False
