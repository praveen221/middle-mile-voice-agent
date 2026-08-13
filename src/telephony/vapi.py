"""Vapi outbound — the same-day phone path while Exotel Voicebot is wired."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from src.agent.prompts import build_system_prompt
from src.agent.state import NegotiationSession
from src.config import Settings, get_settings

VAPI_API = "https://api.vapi.ai"


class VapiError(RuntimeError):
    pass


@dataclass(frozen=True)
class VapiCall:
    id: str
    status: str
    raw: dict[str, Any]


class VapiClient:
    def __init__(
        self,
        settings: Settings | None = None,
        *,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self._transport = transport

    def _headers(self) -> dict[str, str]:
        if not self.settings.vapi_api_key:
            raise VapiError("VAPI_API_KEY is required")
        return {
            "Authorization": f"Bearer {self.settings.vapi_api_key}",
            "Content-Type": "application/json",
        }

    def _client(self) -> httpx.Client:
        return httpx.Client(timeout=30.0, transport=self._transport, headers=self._headers())

    def create_outbound(
        self,
        to_number: str,
        *,
        session: NegotiationSession | None = None,
        assistant_id: str | None = None,
        first_message: str | None = None,
    ) -> VapiCall:
        """Place an outbound PSTN call.

        Uses a saved Vapi assistant when VAPI_ASSISTANT_ID is set, otherwise a
        transient assistant with this repo's Hinglish coordinator prompt.
        """
        if not self.settings.vapi_phone_number_id:
            raise VapiError("VAPI_PHONE_NUMBER_ID is required")

        payload: dict[str, Any] = {
            "phoneNumberId": self.settings.vapi_phone_number_id,
            "customer": {"number": to_number},
        }
        saved = assistant_id or self.settings.vapi_assistant_id
        if saved:
            payload["assistantId"] = saved
        else:
            prompt = (
                build_system_prompt(session)
                if session is not None
                else "You are a Hinglish middle-mile logistics coordinator on a phone call. Keep turns short."
            )
            payload["assistant"] = {
                "name": "middle-mile-coordinator",
                "firstMessage": first_message
                or "Namaste, main middle-mile desk se bol raha hoon. Ek minute lagega?",
                "model": {
                    "provider": "google",
                    "model": self.settings.llm_model,
                    "messages": [{"role": "system", "content": prompt}],
                },
            }

        with self._client() as client:
            response = client.post(f"{VAPI_API}/call/phone", json=payload)
        return self._parse(response)

    def _parse(self, response: httpx.Response) -> VapiCall:
        try:
            body = response.json()
        except ValueError as exc:
            raise VapiError(f"Vapi returned non-JSON ({response.status_code}): {response.text}") from exc
        if response.is_error:
            raise VapiError(f"Vapi HTTP {response.status_code}: {body}")
        call_id = str(body.get("id") or "")
        if not call_id:
            raise VapiError(f"Vapi response missing id: {body}")
        return VapiCall(id=call_id, status=str(body.get("status") or "unknown"), raw=body)
