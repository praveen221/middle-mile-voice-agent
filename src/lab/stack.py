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


def save_stack(stack: VoiceStack, path: Path | None = None) -> Path:
    target = path or stack_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(stack.model_dump_json(indent=2), encoding="utf-8")
    return target


def load_stack(path: Path | None = None) -> VoiceStack:
    target = path or stack_path()
    if not target.exists():
        return VoiceStack()
    return VoiceStack.model_validate_json(target.read_text(encoding="utf-8"))


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
    return VoiceStack.model_validate(merged)
