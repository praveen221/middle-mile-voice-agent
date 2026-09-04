from src.tools.status import get_record_status


def test_known_record():
    row = get_record_status("bk-1001")
    assert row["found"] is True
    assert row["origin"] == "ANDHERI"
    assert row["destination"] == "BANDRA"
    assert row["vendor_phone"].startswith("+91")
    assert row["vendor_name"] == "Asha"
    assert row["gate_out_latest"] == "15:30"


def test_missing_record():
    row = get_record_status("NOPE")
    assert row["found"] is False
