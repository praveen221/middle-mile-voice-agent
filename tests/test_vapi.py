import json

import httpx
import pytest

from src.agent.state import NegotiationSession, Party
from src.config import Settings
from src.telephony.vapi import VapiClient, VapiError


def test_create_outbound_transient_assistant():
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "https://api.vapi.ai/call/phone"
        assert request.headers["authorization"] == "Bearer vapi-secret"
        payload = json.loads(request.content)
        assert payload["customer"]["number"] == "+919800000001"
        assert payload["phoneNumberId"] == "pn-1"
        assert "assistant" in payload
        return httpx.Response(201, json={"id": "call-9", "status": "queued"})

    client = VapiClient(
        settings=Settings(_env_file=None, vapi_api_key="vapi-secret", vapi_phone_number_id="pn-1"),
        transport=httpx.MockTransport(handler),
    )
    session = NegotiationSession(session_id="s1", current_party=Party.VENDOR)
    call = client.create_outbound("+919800000001", session=session)
    assert call.id == "call-9"


def test_missing_key():
    client = VapiClient(settings=Settings(_env_file=None))
    with pytest.raises(VapiError):
        client.create_outbound("+9198")
