"""Persist one local eval session so you can replay warehouse after driver."""

from __future__ import annotations

import os
from pathlib import Path

from src.agent.state import NegotiationSession

DEFAULT_PATH = Path(".local/last-session.json")


def session_path() -> Path:
    return Path(os.environ.get("MM_SESSION_FILE", str(DEFAULT_PATH)))


def load_session(path: Path | None = None) -> NegotiationSession | None:
    target = path or session_path()
    if not target.exists():
        return None
    return NegotiationSession.model_validate_json(target.read_text(encoding="utf-8"))


def save_session(session: NegotiationSession, path: Path | None = None) -> Path:
    target = path or session_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(session.model_dump_json(indent=2), encoding="utf-8")
    return target
