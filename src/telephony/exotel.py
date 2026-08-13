"""Exotel Voice v1 client for sequential outbound calls."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from src.config import Settings, get_settings


class ExotelError(RuntimeError):
    pass


@dataclass(frozen=True)
class ExotelCall:
    sid: str
    status: str
    raw: dict[str, Any]


class ExotelClient:
    def __init__(
        self,
        settings: Settings | None = None,
        *,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self._transport = transport

    @property
    def base_url(self) -> str:
        host = self.settings.exotel_subdomain.strip() or "api.exotel.com"
        host = host.removeprefix("https://").removeprefix("http://")
        return f"https://{host}/v1/Accounts/{self.settings.exotel_sid}"

    def flow_url(self, app_id: str | None = None) -> str:
        sid = self.settings.exotel_sid
        app = app_id or self.settings.exotel_app_id
        if not sid or not app:
            raise ExotelError("EXOTEL_SID and EXOTEL_APP_ID are required to build a flow URL")
        return f"http://my.exotel.com/{sid}/exoml/start_voice/{app}"

    def _auth(self) -> tuple[str, str]:
        key = self.settings.exotel_api_key
        token = self.settings.exotel_token
        if not key or not token:
            raise ExotelError("EXOTEL_API_KEY and EXOTEL_TOKEN are required")
        return key, token

    def _client(self) -> httpx.Client:
        return httpx.Client(
            timeout=30.0,
            transport=self._transport,
            auth=self._auth(),
        )

    def connect_to_flow(
        self,
        to_number: str,
        *,
        caller_id: str | None = None,
        app_id: str | None = None,
        custom_field: str | None = None,
        status_callback: str | None = None,
        time_limit: int | None = 600,
    ) -> ExotelCall:
        """Call `to_number` and drop them into an Exotel Voicebot / flow applet."""
        payload: dict[str, Any] = {
            "From": to_number,
            "CallerId": caller_id or self.settings.exotel_from_number,
            "Url": self.flow_url(app_id),
            "CallType": "trans",
        }
        if not payload["CallerId"]:
            raise ExotelError("EXOTEL_FROM_NUMBER (CallerId / ExoPhone) is required")
        if custom_field:
            payload["CustomField"] = custom_field
        if status_callback:
            payload["StatusCallback"] = status_callback
        if time_limit:
            payload["TimeLimit"] = time_limit

        with self._client() as client:
            response = client.post(f"{self.base_url}/Calls/connect", data=payload)
        return self._parse(response)

    def get_call(self, call_sid: str) -> ExotelCall:
        with self._client() as client:
            response = client.get(f"{self.base_url}/Calls/{call_sid}.json", params={"details": "true"})
        return self._parse(response)

    def _parse(self, response: httpx.Response) -> ExotelCall:
        try:
            body = response.json()
        except ValueError as exc:
            raise ExotelError(f"Exotel returned non-JSON ({response.status_code}): {response.text}") from exc
        if response.is_error:
            raise ExotelError(f"Exotel HTTP {response.status_code}: {body}")
        call = body.get("Call") or body
        sid = str(call.get("Sid") or "")
        status = str(call.get("Status") or "unknown")
        if not sid:
            raise ExotelError(f"Exotel response missing Call.Sid: {body}")
        return ExotelCall(sid=sid, status=status, raw=body)
