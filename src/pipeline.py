"""Assemble the Pipecat STT → LLM → TTS voice loop."""

from __future__ import annotations

import os
from typing import Any

from src.agent.coordinator import Coordinator
from src.agent.prompts import build_system_prompt, opening_line
from src.agent.state import NegotiationSession
from src.config import Settings, get_settings
from src.tools.bindings import make_voice_tools


def build_stt(settings: Settings):
    provider = settings.resolved_stt()
    if provider == "sarvam":
        from pipecat.services.sarvam.stt import SarvamSTTService

        return SarvamSTTService(
            api_key=settings.sarvam_api_key,
            settings=SarvamSTTService.Settings(model="saaras:v3"),
        )

    from pipecat.services.deepgram.stt import DeepgramSTTService

    return DeepgramSTTService(api_key=settings.deepgram_api_key)


def build_tts(settings: Settings):
    provider = settings.resolved_tts()
    if provider == "sarvam":
        from pipecat.services.sarvam.tts import SarvamTTSService

        return SarvamTTSService(
            api_key=settings.sarvam_api_key,
            settings=SarvamTTSService.Settings(
                model="bulbul:v3",
                voice=settings.sarvam_tts_voice,
            ),
        )

    from pipecat.services.azure.tts import AzureTTSService
    from pipecat.transcriptions.language import Language

    language = getattr(Language, "HI_IN", None) or getattr(Language, "HI")
    return AzureTTSService(
        api_key=settings.azure_speech_key,
        region=settings.azure_speech_region,
        settings=AzureTTSService.Settings(
            voice=settings.azure_tts_voice,
            language=language,
        ),
    )


def build_llm(settings: Settings, system_instruction: str):
    from pipecat.services.google.llm import GoogleLLMService

    settings.require_llm()
    return GoogleLLMService(
        api_key=settings.google_api_key,
        settings=GoogleLLMService.Settings(
            model=settings.llm_model,
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
    logger.info(
        "Starting middle-mile bot session={} party={} stt={} tts={}",
        session.session_id,
        session.current_party,
        settings.resolved_stt(),
        settings.resolved_tts(),
    )

    stt = build_stt(settings)
    tts = build_tts(settings)
    llm = build_llm(settings, build_system_prompt(session))
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
    worker = PipelineWorker(
        pipeline,
        params=PipelineParams(enable_metrics=True, enable_usage_metrics=True),
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
                    f"then continue the negotiation: {opening_line(session.current_party, session)}"
                ),
            }
        )
        await worker.queue_frames([LLMRunFrame()])

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info("Client disconnected")
        await runner.cancel()

    await runner.run()


def bootstrap_session(
    session_id: str | None = None,
    *,
    shipment_id: str | None = None,
    origin: str | None = None,
    destination: str | None = None,
    vehicle_type: str | None = None,
    pickup_date: str | None = None,
) -> NegotiationSession:
    coordinator = Coordinator()
    sid = session_id or os.environ.get("SESSION_ID") or "local-dev"
    if shipment_id:
        from src.tools.status import get_shipment_status

        info = get_shipment_status(shipment_id)
        if info.get("found"):
            origin = origin or info.get("origin")
            destination = destination or info.get("destination")
            vehicle_type = vehicle_type or info.get("vehicle_type")
            pickup_date = pickup_date or info.get("pickup_date")
    return coordinator.start(
        sid,
        shipment_id=shipment_id,
        origin=origin,
        destination=destination,
        vehicle_type=vehicle_type,
        pickup_date=pickup_date,
    )
