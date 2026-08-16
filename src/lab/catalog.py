"""What the Lab dropdowns can offer, given keys in .env."""

from __future__ import annotations

import time
from typing import Any

import httpx

from src.config import get_settings

FAVORITE_LLMS = [
    {"id": "qwen/qwen3-235b-a22b-2507", "name": "Qwen3 235B Instruct"},
    {"id": "google/gemini-2.5-flash", "name": "Gemini 2.5 Flash"},
    {"id": "sarvam-105b", "name": "Sarvam 105B (native Indic)"},
    {"id": "moonshotai/kimi-k2.5", "name": "Kimi K2.5"},
    {"id": "deepseek/deepseek-v3.2", "name": "DeepSeek V3.2"},
]

# Values sent to the bot stay ISO codes. Labels are what the Lab shows.
LANGUAGE_NAMES: dict[str, str] = {
    "en": "English",
    "hi": "Hindi",
    "mr": "Marathi",
    "gu": "Gujarati",
    "ta": "Tamil",
    "te": "Telugu",
    "kn": "Kannada",
    "ml": "Malayalam",
    "bn": "Bengali",
    "pa": "Punjabi",
    "or": "Odia",
    "multi": "Multilingual (auto)",
    "en-IN": "English (India)",
    "hi-IN": "Hindi (India)",
    "mr-IN": "Marathi (India)",
    "gu-IN": "Gujarati (India)",
    "ta-IN": "Tamil (India)",
    "te-IN": "Telugu (India)",
    "bn-IN": "Bengali (India)",
}

INDIC_CORE = ("hi", "en", "mr", "gu", "ta", "te", "kn", "ml", "bn", "pa", "or")
# Nova-3 STT: Hindi + several Indic. No Malayalam or Odia on Deepgram.
DEEPGRAM_STT = ("en", "hi", "bn", "gu", "kn", "mr", "pa", "ta", "te", "multi")
# Sonic 3.5 TTS: nine Indic languages. No Odia.
CARTESIA_TTS = ("en", "hi", "ta", "te", "bn", "gu", "kn", "ml", "mr", "pa")
# Smallest lists Tamil / Malayalam / Odia as beta.
SMALLEST_SPEECH = ("en", "hi", "ta", "ml", "or", "mr", "gu", "bn", "te", "kn")
AZURE_SPEECH = ("hi-IN", "mr-IN", "gu-IN", "ta-IN", "te-IN", "en-IN", "bn-IN")


def langs(*codes: str) -> list[dict[str, str]]:
    return [{"id": code, "label": LANGUAGE_NAMES.get(code, code)} for code in codes]


STT_OPTIONS = [
    {
        "id": "sarvam",
        "label": "Sarvam Saaras",
        "key": "sarvam_api_key",
        "models": [{"id": "saaras:v3", "label": "saaras:v3 (22 Indic + EN)"}],
        "languages": langs(*INDIC_CORE),
        "indic": True,
    },
    {
        "id": "deepgram",
        "label": "Deepgram Nova",
        "key": "deepgram_api_key",
        "models": [{"id": "nova-3", "label": "nova-3"}],
        "languages": langs(*DEEPGRAM_STT),
        "indic": True,
        "note": "Nova-3 hears Hindi, Bengali, Gujarati, Kannada, Marathi, Punjabi, Tamil, Telugu. No Malayalam or Odia.",
    },
    {
        "id": "azure",
        "label": "Azure Speech",
        "key": "azure_speech_key",
        "models": [{"id": "latest", "label": "Azure latest"}],
        "languages": langs(*AZURE_SPEECH),
        "indic": True,
    },
    {
        "id": "cartesia",
        "label": "Cartesia Ink",
        "key": "cartesia_api_key",
        "models": [{"id": "ink-whisper", "label": "ink-whisper"}],
        "languages": langs("en"),
        "indic": False,
        "note": "Ink STT is English-only. Use Sarvam or Smallest to hear Indian languages.",
    },
    {
        "id": "smallest",
        "label": "Smallest Pulse (STT)",
        "key": "smallest_api_key",
        "models": [{"id": "pulse", "label": "Pulse"}],
        "languages": langs(*SMALLEST_SPEECH),
        "indic": True,
        "note": "Tamil, Malayalam, Odia are beta on Smallest.",
    },
]

TTS_OPTIONS = [
    {
        "id": "sarvam",
        "label": "Sarvam Bulbul",
        "key": "sarvam_api_key",
        "models": [{"id": "bulbul:v3", "label": "bulbul:v3"}],
        "voices": [{"id": "shubh", "label": "shubh"}, {"id": "anushka", "label": "anushka"}],
        "languages": langs(*INDIC_CORE),
        "indic": True,
    },
    {
        "id": "azure",
        "label": "Azure Neural",
        "key": "azure_speech_key",
        "models": [{"id": "neural", "label": "Neural"}],
        "voices": [
            {"id": "hi-IN-SwaraNeural", "label": "Hindi Swara"},
            {"id": "mr-IN-AarohiNeural", "label": "Marathi Aarohi"},
            {"id": "gu-IN-DhwaniNeural", "label": "Gujarati Dhwani"},
            {"id": "ta-IN-PallaviNeural", "label": "Tamil Pallavi"},
        ],
        "languages": langs("hi-IN", "mr-IN", "gu-IN", "ta-IN", "en-IN"),
        "indic": True,
    },
    {
        "id": "deepgram",
        "label": "Deepgram Aura",
        "key": "deepgram_api_key",
        "models": [{"id": "aura-2", "label": "aura-2"}],
        "voices": [{"id": "aura-asteria-en", "label": "asteria-en"}],
        "languages": langs("en"),
        "indic": False,
        "note": "Aura TTS has no Indian languages (English, Spanish, some EU/JP). Use Sarvam, Smallest, or Cartesia to speak Hindi.",
    },
    {
        "id": "cartesia",
        "label": "Cartesia Sonic",
        "key": "cartesia_api_key",
        "models": [{"id": "sonic-3.5", "label": "sonic-3.5"}],
        "voices": [{"id": "71a7ad14-091c-4e8e-a314-022ece01c121", "label": "default"}],
        "languages": langs(*CARTESIA_TTS),
        "indic": True,
        "note": "Sonic 3.5 speaks Hindi, Tamil, Telugu, Bengali, Gujarati, Kannada, Malayalam, Marathi, Punjabi. No Odia.",
    },
    {
        "id": "smallest",
        "label": "Smallest Lightning (TTS)",
        "key": "smallest_api_key",
        "models": [
            {"id": "lightning_v3.1", "label": "lightning v3.1"},
            {"id": "lightning_v3.1_pro", "label": "lightning v3.1 pro"},
        ],
        "voices": [
            {"id": "sophia", "label": "sophia"},
            {"id": "meher", "label": "meher (Indic-leaning)"},
        ],
        "languages": langs(*SMALLEST_SPEECH),
        "indic": True,
        "note": "Tamil, Malayalam, Odia are beta on Smallest.",
    },
]

_LLM_CACHE: tuple[float, list[dict[str, Any]]] | None = None


def key_status() -> dict[str, bool]:
    s = get_settings()
    return {
        "sarvam": bool(s.sarvam_api_key),
        "openrouter": bool(s.openrouter_api_key),
        "google": bool(s.google_api_key),
        "deepgram": bool(s.deepgram_api_key),
        "azure": bool(s.azure_speech_key and s.azure_speech_region),
        "cartesia": bool(s.cartesia_api_key),
        "smallest": bool(s.smallest_api_key),
        "daily": bool(s.daily_api_key),
        "exotel": bool(s.exotel_sid and s.exotel_api_key and s.exotel_token),
        "vapi": bool(s.vapi_api_key),
    }


def _enabled(option: dict[str, Any], keys: dict[str, bool]) -> bool:
    field = option["key"]
    mapping = {
        "sarvam_api_key": "sarvam",
        "deepgram_api_key": "deepgram",
        "azure_speech_key": "azure",
        "cartesia_api_key": "cartesia",
        "smallest_api_key": "smallest",
    }
    return keys.get(mapping.get(field, ""), False)


def speech_catalog() -> dict[str, Any]:
    keys = key_status()
    stt = [{**o, "enabled": _enabled(o, keys)} for o in STT_OPTIONS]
    tts = [{**o, "enabled": _enabled(o, keys)} for o in TTS_OPTIONS]
    return {"keys": keys, "stt": stt, "tts": tts, "llm_favorites": FAVORITE_LLMS}


def openrouter_models() -> list[dict[str, Any]]:
    global _LLM_CACHE
    now = time.time()
    if _LLM_CACHE and now - _LLM_CACHE[0] < 600:
        return _LLM_CACHE[1]
    settings = get_settings()
    if not settings.openrouter_api_key:
        return FAVORITE_LLMS
    try:
        with httpx.Client(timeout=20.0) as client:
            res = client.get(
                "https://openrouter.ai/api/v1/models",
                headers={"Authorization": f"Bearer {settings.openrouter_api_key}"},
                params={"limit": 500},
            )
            res.raise_for_status()
            raw = res.json().get("data") or []
    except Exception:
        return FAVORITE_LLMS
    out: list[dict[str, Any]] = []
    for row in raw:
        mid = row.get("id") or ""
        if not mid:
            continue
        out.append({"id": mid, "name": row.get("name") or mid})
    out.sort(key=lambda x: x["id"])
    _LLM_CACHE = (now, out)
    return out
