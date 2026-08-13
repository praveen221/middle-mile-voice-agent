import json
from urllib.parse import parse_qs

import httpx
import pytest

from src.config import Settings
from src.telephony.exotel import ExotelClient, ExotelError


def _settings(**overrides) -> Settings:
    values = dict(
        exotel_sid="sid123",
        exotel_api_key="key",
        exotel_token="token",
        exotel_subdomain="api.in.exotel.com",
        exotel_from_number="08000000000",
        exotel_app_id="926",
    )
    values.update(overrides)
    return Settings(_env_file=None, **values)


def test_flow_url_and_base():
    client = ExotelClient(settings=_settings())
    assert client.base_url == "https://api.in.exotel.com/v1/Accounts/sid123"
    assert client.flow_url() == "http://my.exotel.com/sid123/exoml/start_voice/926"


def test_connect_to_flow_posts_form():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/Calls/connect")
        body = {k: v[0] for k, v in parse_qs(request.content.decode()).items()}
        assert body["From"] == "+919800000001"
        assert "start_voice" in body["Url"]
        return httpx.Response(
            200,
            json={"Call": {"Sid": "call-1", "Status": "in-progress"}},
        )

    client = ExotelClient(settings=_settings(), transport=httpx.MockTransport(handler))
    call = client.connect_to_flow("+919800000001", custom_field=json.dumps({"session_id": "s1"}))
    assert call.sid == "call-1"
    assert call.status == "in-progress"


def test_missing_keys_raise():
    client = ExotelClient(settings=_settings(exotel_api_key="", exotel_token=""))
    with pytest.raises(ExotelError):
        client.connect_to_flow("+9198")
