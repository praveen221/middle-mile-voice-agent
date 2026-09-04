#!/usr/bin/env python3
"""Lab shell: dropdowns on top, Pipecat Playground in the frame.

    Terminal 1:  python scripts/run_local.py
    Terminal 2:  python scripts/run_lab.py
    Open:        http://localhost:3000
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env", override=True)

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import uvicorn

from src.eval.db import CallDB
from src.lab.catalog import openrouter_models, speech_catalog
from src.lab.situation import LabSituation, load_situation, presets, save_situation
from src.lab.stack import VoiceStack, load_stack, normalize_stack, save_stack

app = FastAPI(title="voice-agent lab")


class StackIn(BaseModel):
    stt: str
    stt_language: str = "hi"
    tts: str
    tts_language: str = "hi"
    tts_voice: str = "shubh"
    tts_model: str | None = None
    stt_model: str | None = None
    llm_model: str
    llm_provider: str = "openrouter"
    situation: LabSituation | None = None


def _db() -> CallDB:
    return CallDB()


def _call_payload(db: CallDB, call_id: int) -> dict | None:
    summary = db.call_summary(call_id)
    call = summary["call"]
    if not call:
        return None
    transcript = call.get("transcript") or db.compose_transcript(call_id)
    return {
        "id": call.get("id"),
        "config_id": call.get("config_id"),
        "started_at": call.get("started_at"),
        "ended_at": call.get("ended_at"),
        "status": call.get("status"),
        "tester_name": call.get("tester_name"),
        "situation_title": call.get("situation_title"),
        "llm_model": call.get("llm_model"),
        "stt": call.get("stt"),
        "tts": call.get("tts"),
        "prompt": call.get("prompt"),
        "transcript": transcript,
        "utterances": summary["utterances"],
        "tools": summary["tools"],
    }


@app.get("/")
def lab_page():
    return FileResponse(ROOT / "web" / "lab.html")


@app.get("/api/catalog")
def catalog():
    db = _db()
    data = speech_catalog()
    data["llm_all"] = openrouter_models()
    data["situation"] = load_situation().model_dump()
    data["presets"] = [row.model_dump() for row in presets()]
    data["stack"] = load_stack().model_dump()
    active_id = db.active_config_id()
    data["active_config_id"] = active_id
    data["active_config"] = db.get_config(active_id) if active_id else None
    data["configs"] = db.list_configs()
    return data


@app.get("/api/situation")
def get_situation():
    return load_situation().model_dump()


@app.get("/api/configs")
def list_configs():
    db = _db()
    return {"active_config_id": db.active_config_id(), "configs": db.list_configs()}


@app.get("/api/calls")
def list_calls(config_id: int | None = None):
    db = _db()
    cid = config_id if config_id is not None else db.active_config_id()
    return {
        "config_id": cid,
        "active_config_id": db.active_config_id(),
        "calls": db.list_calls(config_id=cid),
    }


@app.get("/api/calls/last")
def last_call():
    db = _db()
    last = db.last_call()
    if last is None:
        return JSONResponse({"ok": False, "call": None})
    return {"ok": True, "call": _call_payload(db, int(last["id"]))}


@app.get("/api/calls/{call_id}")
def get_call(call_id: int):
    db = _db()
    payload = _call_payload(db, call_id)
    if payload is None:
        return JSONResponse({"ok": False, "call": None}, status_code=404)
    return {"ok": True, "call": payload}


@app.post("/api/stack")
def set_stack(body: StackIn):
    stack = normalize_stack(
        VoiceStack(
            stt=body.stt,
            stt_model=body.stt_model or "",
            stt_language=body.stt_language,
            tts=body.tts,
            tts_model=body.tts_model or "",
            tts_language=body.tts_language,
            tts_voice=body.tts_voice,
            llm_model=body.llm_model,
            llm_provider=body.llm_provider,
        )
    )
    path = save_stack(stack)
    if body.situation is not None:
        save_situation(body.situation)
    situation = load_situation()
    config = _db().save_config(stack=stack.model_dump(), situation=situation.model_dump())
    return JSONResponse(
        {
            "ok": True,
            "path": str(path),
            "stack": stack.model_dump(),
            "situation": situation.model_dump(),
            "config": config,
        }
    )


if __name__ == "__main__":
    print("Lab UI  →  http://localhost:3000")
    print("Playground must also be running: python scripts/run_local.py")
    uvicorn.run(app, host="0.0.0.0", port=3000)
