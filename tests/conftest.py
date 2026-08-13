from __future__ import annotations

import pytest

from src.agent.state import InMemorySessionStore, reset_store


@pytest.fixture(autouse=True)
def isolated_store(monkeypatch):
    store = InMemorySessionStore()
    reset_store()
    monkeypatch.setattr("src.agent.state._STORE", store)
    monkeypatch.setattr("src.agent.coordinator.get_store", lambda redis_url="": store)
    yield store
    reset_store()
