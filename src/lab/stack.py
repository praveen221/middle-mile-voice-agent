"""Active STT / LLM / TTS stack for the next Playground connect."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field

STACK_PATH = Path(".local/lab-stack.json")


class VoiceStack(BaseModel):
    stt: str = "sarvam"
    stt_model: str = "saaras:v3"
    stt_language: str = "hi"
    tts: str = "sarvam"
    tts_model: str = "bulbul:v3"
    tts_voice: str = "shubh"
    tts_language: str = "hi"
    llm_provider: str = "openrouter"
    llm_model: str = "qwen/qwen3-235b-a22b-2507"


def stack_path() -> Path:
    import os

    return Path(os.environ.get("MM_LAB_STACK", str(STACK_PATH)))


def _vendor_first(kind: str, vendor: str, field: str) -> str | None:
    from src.lab.catalog import STT_OPTIONS, TTS_OPTIONS

    options = STT_OPTIONS if kind == "stt" else TTS_OPTIONS
    row = next((item for item in options if item["id"] == vendor), None)
    items = (row or {}).get(field) or []
    if not items:
        return None
    first = items[0]
    return first["id"] if isinstance(first, dict) else first


def _vendor_ids(kind: str, vendor: str, field: str) -> set[str]:
    from src.lab.catalog import STT_OPTIONS, TTS_OPTIONS

    options = STT_OPTIONS if kind == "stt" else TTS_OPTIONS
    row = next((item for item in options if item["id"] == vendor), None)
    items = (row or {}).get(field) or []
    out: set[str] = set()
    for item in items:
        out.add(item["id"] if isinstance(item, dict) else item)
    return out


def normalize_stack(stack: VoiceStack) -> VoiceStack:
    """Drop leftover Sarvam model names when the vendor is Smallest / Cartesia / etc."""
    data = stack.model_dump()
    stt_models = _vendor_ids("stt", data["stt"], "models")
    tts_models = _vendor_ids("tts", data["tts"], "models")
    tts_voices = _vendor_ids("tts", data["tts"], "voices")
    if stt_models and data.get("stt_model") not in stt_models:
        data["stt_model"] = _vendor_first("stt", data["stt"], "models") or data["stt_model"]
    if tts_models and data.get("tts_model") not in tts_models:
        data["tts_model"] = _vendor_first("tts", data["tts"], "models") or data["tts_model"]
    if tts_voices and data.get("tts_voice") not in tts_voices:
        data["tts_voice"] = _vendor_first("tts", data["tts"], "voices") or data["tts_voice"]
    return VoiceStack.model_validate(data)


def save_stack(stack: VoiceStack, path: Path | None = None) -> Path:
    target = path or stack_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    stack = normalize_stack(stack)
    target.write_text(stack.model_dump_json(indent=2), encoding="utf-8")
    return target


def load_stack(path: Path | None = None) -> VoiceStack:
    target = path or stack_path()
    if not target.exists():
        return VoiceStack()
    return normalize_stack(VoiceStack.model_validate_json(target.read_text(encoding="utf-8")))


def stack_from_mapping(data: object) -> VoiceStack:
    if not isinstance(data, dict):
        return load_stack()
    if not data:
        return load_stack()
    current = load_stack()
    merged = current.model_dump()
    for key in VoiceStack.model_fields:
        if key in data and data[key] not in (None, ""):
            merged[key] = data[key]
    return normalize_stack(VoiceStack.model_validate(merged))
