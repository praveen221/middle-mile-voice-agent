"""Assemble the Pipecat STT → LLM → TTS voice loop."""

from __future__ import annotations

import os
from typing import Any

from src.agent.coordinator import Coordinator
from src.agent.prompts import build_system_prompt, opening_line
from src.agent.state import NegotiationSession, Party, PartyOutcome, get_store
from src.config import Settings, get_settings
from src.eval.db import CallDB
from src.eval.debrief import debrief, format_debrief
from src.eval.recorder import CallRecorder
from src.eval.seed import seed_kimi_baseline
from src.eval.session_file import save_session
from src.lab.situation import load_situation
from src.lab.stack import VoiceStack, stack_from_mapping
from src.scenarios import get_scenario
from src.tools.bindings import make_voice_tools


def _lang(code: str):
    from pipecat.transcriptions.language import Language

    raw_code = (code or "hi").strip()
    if raw_code.lower() == "multi":
        return "multi"
    raw = raw_code.replace("-", "_").upper()
    return getattr(Language, raw, None) or getattr(Language, raw.split("_")[0], None) or Language.HI


def build_stt(settings: Settings, stack: VoiceStack | None = None):
    provider = stack.stt if stack else settings.resolved_stt()
    language = _lang(stack.stt_language if stack else "hi")
    if provider == "sarvam":
        from pipecat.services.sarvam.stt import SarvamSTTService

        return SarvamSTTService(
            api_key=settings.sarvam_api_key,
            settings=SarvamSTTService.Settings(model="saaras:v3", language=language),
        )
    if provider == "azure":
        from pipecat.services.azure.stt import AzureSTTService

        return AzureSTTService(
            api_key=settings.azure_speech_key,
            region=settings.azure_speech_region,
            settings=AzureSTTService.Settings(language=language),
        )
    if provider == "cartesia":
        from pipecat.services.cartesia.stt import CartesiaSTTService

        return CartesiaSTTService(api_key=settings.cartesia_api_key)
    if provider == "smallest":
        from pipecat.services.smallest.stt import SmallestSTTService

        return SmallestSTTService(
            api_key=settings.smallest_api_key,
            settings=SmallestSTTService.Settings(language=language),
        )
    from pipecat.services.deepgram.stt import DeepgramSTTService

    return DeepgramSTTService(
        api_key=settings.deepgram_api_key,
        settings=DeepgramSTTService.Settings(model="nova-3", language=language),
    )


def build_tts(settings: Settings, stack: VoiceStack | None = None):
    provider = stack.tts if stack else settings.resolved_tts()
    language = _lang(stack.tts_language if stack else "hi")
    if provider == "sarvam":
        from pipecat.services.sarvam.tts import SarvamTTSService

        voice = (stack.tts_voice if stack else None) or settings.sarvam_tts_voice
        return SarvamTTSService(
            api_key=settings.sarvam_api_key,
            settings=SarvamTTSService.Settings(model="bulbul:v3", voice=voice, language=language),
        )
    if provider == "deepgram":
        from pipecat.services.deepgram.tts import DeepgramTTSService

        return DeepgramTTSService(api_key=settings.deepgram_api_key)
    if provider == "cartesia":
        from pipecat.services.cartesia.tts import CartesiaTTSService

        voice = (stack.tts_voice if stack else None) or "71a7ad14-091c-4e8e-a314-022ece01c121"
        return CartesiaTTSService(
            api_key=settings.cartesia_api_key,
            settings=CartesiaTTSService.Settings(
                model="sonic-3.5",
                voice=voice,
                language=language,
            ),
        )
    if provider == "smallest":
        from pipecat.services.smallest.tts import SmallestTTSService

        voice = (stack.tts_voice if stack else None) or "meher"
        raw_model = stack.tts_model if stack else None
        model = raw_model if raw_model and raw_model.startswith("lightning") else "lightning_v3.1"
        return SmallestTTSService(
            api_key=settings.smallest_api_key,
            settings=SmallestTTSService.Settings(voice=voice, language=language, model=model),
        )
    from pipecat.services.azure.tts import AzureTTSService

    voice = (stack.tts_voice if stack else None) or settings.azure_tts_voice
    return AzureTTSService(
        api_key=settings.azure_speech_key,
        region=settings.azure_speech_region,
        settings=AzureTTSService.Settings(voice=voice, language=language),
    )


def build_llm(settings: Settings, system_instruction: str, stack: VoiceStack | None = None):
    model = (stack.llm_model if stack else None) or settings.llm_model
    provider = (stack.llm_provider if stack else None) or settings.resolved_llm()
    if model == "sarvam-105b" or provider == "sarvam":
        from pipecat.services.sarvam.llm import SarvamLLMService

        return SarvamLLMService(
            api_key=settings.sarvam_api_key,
            settings=SarvamLLMService.Settings(
                model="sarvam-105b",
                system_instruction=system_instruction,
            ),
        )
    if settings.openrouter_api_key and provider != "google":
        from pipecat.services.openrouter.llm import OpenRouterLLMService

        return OpenRouterLLMService(
            api_key=settings.openrouter_api_key,
            settings=OpenRouterLLMService.Settings(
                model=model,
                system_instruction=system_instruction,
            ),
        )

    from pipecat.services.google.llm import GoogleLLMService

    if model.startswith("google/"):
        model = model.split("/", 1)[1]
    return GoogleLLMService(
        api_key=settings.google_api_key,
        settings=GoogleLLMService.Settings(
            model=model,
            system_instruction=system_instruction,
        ),
    )


def transport_params() -> dict[str, Any]:
    from pipecat.transports.base_transport import TransportParams
    from pipecat.transports.daily.transport import DailyParams
    from pipecat.transports.websocket.fastapi import FastAPIWebsocketParams

    audio = dict(audio_in_enabled=True, audio_out_enabled=True)
    params: dict[str, Any] = {
        "daily": lambda: DailyParams(**audio),
        "twilio": lambda: FastAPIWebsocketParams(**audio),
        "webrtc": lambda: TransportParams(**audio),
    }
    try:
        from pipecat.evals.transport import EvalTransportParams

        params["eval"] = lambda: EvalTransportParams(**audio)
    except ImportError:
        pass
    return params


async def run_bot(transport, runner_args, session: NegotiationSession) -> None:
    from loguru import logger
    from pipecat.audio.vad.silero import SileroVADAnalyzer
    from pipecat.frames.frames import LLMRunFrame
    from pipecat.pipeline.pipeline import Pipeline
    from pipecat.pipeline.worker import PipelineParams, PipelineWorker
    from pipecat.processors.aggregators.llm_context import LLMContext
    from pipecat.processors.aggregators.llm_response_universal import (
        LLMContextAggregatorPair,
        LLMUserAggregatorParams,
    )
    from pipecat.workers.runner import WorkerRunner

    settings = get_settings()
    stack = stack_from_mapping(getattr(runner_args, "body", None))
    situation = load_situation()
    logger.info(
        "Starting middle-mile bot session={} party={} llm={}/{} stt={} tts={} case={}",
        session.session_id,
        session.current_party,
        stack.llm_provider,
        stack.llm_model,
        stack.stt,
        stack.tts,
        situation.title,
    )

    prompt = build_system_prompt(session, situation)
    db = CallDB()
    seed_kimi_baseline(db)
    config = db.save_config(stack=stack.model_dump(), situation=situation.model_dump())
    call_id = db.start_call(
        session_id=session.session_id,
        party=str(session.current_party),
        scenario_id=situation.id or session.scenario_id,
        llm_provider=stack.llm_provider,
        llm_model=stack.llm_model,
        stt=stack.stt,
        tts=stack.tts,
        prompt=prompt,
        snapshot=session.model_dump_json(),
        situation_title=situation.title,
        situation_json=situation.model_dump_json(),
        tester_name=situation.tester_name or None,
        config_id=config["id"],
    )
    logger.info(
        "Recording call_id={} config_id={} reused={} to {}",
        call_id,
        config["id"],
        config.get("reused"),
        db.path,
    )

    stt = build_stt(settings, stack)
    tts = build_tts(settings, stack)
    llm = build_llm(settings, prompt, stack)
    tools = make_voice_tools(session.session_id)

    context = LLMContext(tools=tools)
    user_aggregator, assistant_aggregator = LLMContextAggregatorPair(
        context,
        user_params=LLMUserAggregatorParams(vad_analyzer=SileroVADAnalyzer()),
    )

    pipeline = Pipeline(
        [
            transport.input(),
            stt,
            user_aggregator,
            llm,
            tts,
            transport.output(),
            assistant_aggregator,
        ]
    )
    recorder = CallRecorder(db, call_id)
    observers: list = [recorder]
    try:
        from pipecat.observers.user_bot_latency_observer import UserBotLatencyObserver

        latency = UserBotLatencyObserver()

        @latency.event_handler("on_latency_measured")
        async def _on_turn_latency(_observer, seconds: float):
            db.add_metric(
                call_id,
                kind="user_to_bot",
                processor="turn",
                processing_ms=float(seconds) * 1000.0,
            )
            db.add_event(call_id, "user_to_bot_ms", {"ms": float(seconds) * 1000.0})

        @latency.event_handler("on_first_bot_speech_latency")
        async def _on_first_speech(_observer, seconds: float):
            db.add_metric(
                call_id,
                kind="first_bot_speech",
                processor="turn",
                processing_ms=float(seconds) * 1000.0,
            )

        observers.append(latency)
    except Exception:
        logger.exception("UserBotLatencyObserver not attached")

    worker = PipelineWorker(
        pipeline,
        params=PipelineParams(enable_metrics=True, enable_usage_metrics=True),
        observers=observers,
        idle_timeout_secs=getattr(runner_args, "pipeline_idle_timeout_secs", None),
    )
    runner = WorkerRunner(handle_sigint=getattr(runner_args, "handle_sigint", True))
    await runner.add_workers(worker)

    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        logger.info("Client connected")
        context.add_message(
            {
                "role": "developer",
                "content": (
                    "Call just connected. Greet the current party with this opening, "
                    f"then continue the negotiation: {opening_line(session.current_party, session, situation)}"
                ),
            }
        )
        await worker.queue_frames([LLMRunFrame()])

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info("Client disconnected")
        try:
            latest = get_store().get(session.session_id) or session
            if latest.scenario_id:
                try:
                    report = debrief(latest, get_scenario(latest.scenario_id))
                    print(format_debrief(report), flush=True)
                except KeyError:
                    logger.warning("No debrief scenario for {}", latest.scenario_id)
            save_session(latest)
            db.end_call(call_id, status=latest.status, snapshot=latest.model_dump_json())
            summary = db.call_summary(call_id)
            tokens = summary["tokens"]
            print(
                f"RECORDED call_id={call_id} utterances={len(summary['utterances'])} "
                f"tools={len(summary['tools'])} tokens={tokens['total']} db={db.path}",
                flush=True,
            )
        except Exception:
            logger.exception("Failed to write debrief")
        await runner.cancel()

    await runner.run()


def bootstrap_session(
    session_id: str | None = None,
    *,
    record_id: str | None = None,
    origin: str | None = None,
    destination: str | None = None,
    item_type: str | None = None,
    slot_date: str | None = None,
    party: Party | str | None = None,
    scenario_id: str | None = None,
    shipment_id: str | None = None,
    vehicle_type: str | None = None,
    pickup_date: str | None = None,
) -> NegotiationSession:
    coordinator = Coordinator()
    sid = session_id or os.environ.get("SESSION_ID") or "local-dev"
    record_id = record_id or shipment_id
    item_type = item_type or vehicle_type
    slot_date = slot_date or pickup_date
    scenario = get_scenario(scenario_id) if scenario_id else None
    if scenario is not None:
        record_id = record_id or scenario.record_id
        origin = origin or scenario.origin
        destination = destination or scenario.destination
        item_type = item_type or scenario.item_type
        slot_date = slot_date or scenario.slot_date
    if record_id:
        from src.tools.status import get_record_status

        info = get_record_status(record_id)
        if info.get("found"):
            origin = origin or info.get("origin")
            destination = destination or info.get("destination")
            item_type = item_type or info.get("item_type")
            slot_date = slot_date or info.get("slot_date")
    first_party = Party(party) if party else Party.VENDOR
    session = coordinator.start(
        sid,
        record_id=record_id,
        origin=origin,
        destination=destination,
        item_type=item_type,
        slot_date=slot_date,
        first_party=first_party,
        scenario_id=scenario.id if scenario else scenario_id,
        goal=scenario.success_means if scenario else None,
    )
    if party:
        session.current_party = Party(party)
        session.party_outcomes.setdefault(session.current_party.value, PartyOutcome.PENDING)
        coordinator.store.put(session)
    return session
