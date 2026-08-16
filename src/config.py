"""Load environment-backed settings."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    google_api_key: str = ""
    openrouter_api_key: str = ""
    llm_provider: Literal["sarvam", "openrouter", "google"] = "sarvam"
    llm_model: str = "sarvam-105b"

    sarvam_api_key: str = ""
    deepgram_api_key: str = ""
    cartesia_api_key: str = ""
    smallest_api_key: str = ""
    stt_provider: Literal["sarvam", "deepgram", "azure", "cartesia", "smallest"] = "sarvam"

    azure_speech_key: str = ""
    azure_speech_region: str = ""
    tts_provider: Literal["sarvam", "azure", "deepgram", "cartesia", "smallest"] = "sarvam"
    sarvam_tts_voice: str = "shubh"
    azure_tts_voice: str = "hi-IN-SwaraNeural"

    daily_api_key: str = ""
    daily_room_url: str = ""

    exotel_sid: str = ""
    exotel_token: str = ""
    exotel_api_key: str = ""
    exotel_subdomain: str = "api.exotel.com"
    exotel_from_number: str = ""
    exotel_app_id: str = ""

    vapi_api_key: str = ""
    vapi_phone_number_id: str = ""
    vapi_assistant_id: str = ""

    redis_url: str = ""

    max_party_turns: int = Field(default=12, ge=1)
    max_handoffs: int = Field(default=6, ge=1)

    def resolved_stt(self) -> Literal["sarvam", "deepgram"]:
        if self.stt_provider == "sarvam" and self.sarvam_api_key:
            return "sarvam"
        if self.deepgram_api_key:
            return "deepgram"
        if self.sarvam_api_key:
            return "sarvam"
        raise RuntimeError(
            "No STT key found. Set SARVAM_API_KEY or DEEPGRAM_API_KEY in .env"
        )

    def resolved_tts(self) -> Literal["sarvam", "azure"]:
        if self.tts_provider == "sarvam" and self.sarvam_api_key:
            return "sarvam"
        if self.azure_speech_key and self.azure_speech_region:
            return "azure"
        if self.sarvam_api_key:
            return "sarvam"
        raise RuntimeError(
            "No TTS key found. Set SARVAM_API_KEY or AZURE_SPEECH_KEY + AZURE_SPEECH_REGION"
        )

    def resolved_llm(self) -> Literal["sarvam", "openrouter", "google"]:
        if self.llm_provider == "sarvam" and self.sarvam_api_key:
            return "sarvam"
        if self.llm_provider == "openrouter" and self.openrouter_api_key:
            return "openrouter"
        if self.google_api_key:
            return "google"
        if self.sarvam_api_key:
            return "sarvam"
        if self.openrouter_api_key:
            return "openrouter"
        raise RuntimeError(
            "No LLM key found. Set SARVAM_API_KEY, OPENROUTER_API_KEY, or GOOGLE_API_KEY"
        )

    def require_llm(self) -> str:
        provider = self.resolved_llm()
        if provider == "sarvam":
            return self.sarvam_api_key
        if provider == "openrouter":
            return self.openrouter_api_key
        return self.google_api_key


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
