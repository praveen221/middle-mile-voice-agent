from src.agent.state import NegotiationSession, Party
from src.eval.session_file import load_session, save_session


def test_roundtrip(tmp_path):
    path = tmp_path / "session.json"
    session = NegotiationSession(
        session_id="s1",
        scenario_id="same_day_appointment",
        current_party=Party.WAREHOUSE,
        accepted_rate=23000,
    )
    save_session(session, path)
    loaded = load_session(path)
    assert loaded is not None
    assert loaded.accepted_rate == 23000
    assert loaded.current_party == Party.WAREHOUSE
