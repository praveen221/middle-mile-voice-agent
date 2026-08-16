"""Pipecat observer: transcript, tools, TTFB, tokens, turn latency."""

from __future__ import annotations

import time

from src.eval.db import CallDB


class CallRecorder:
    def __init__(self, db: CallDB, call_id: int) -> None:
        self.db = db
        self.call_id = call_id
        self._seen: set[int] = set()
        self._llm_buf: list[str] = []
        self._tts_buf: list[str] = []
        self._got_llm_turn = False
        self._tool_starts: dict[str, tuple[str, float]] = {}

    def _once(self, frame) -> bool:
        key = id(frame)
        if key in self._seen:
            return False
        self._seen.add(key)
        return True

    async def on_process_frame(self, data) -> None:
        return

    async def on_pipeline_started(self) -> None:
        self.db.add_event(self.call_id, "pipeline_started")

    async def on_push_frame(self, data) -> None:
        frame = data.frame
        if not self._once(frame):
            return

        from pipecat.frames.frames import (
            BotStartedSpeakingFrame,
            BotStoppedSpeakingFrame,
            FunctionCallInProgressFrame,
            FunctionCallResultFrame,
            InterimTranscriptionFrame,
            InterruptionFrame,
            LLMFullResponseEndFrame,
            LLMFullResponseStartFrame,
            LLMTextFrame,
            MetricsFrame,
            TranscriptionFrame,
            TTSTextFrame,
            UserStartedSpeakingFrame,
            UserStoppedSpeakingFrame,
        )
        from pipecat.metrics.metrics import (
            LLMUsageMetricsData,
            ProcessingMetricsData,
            STTUsageMetricsData,
            TextAggregationMetricsData,
            TTFAMetricsData,
            TTFBMetricsData,
            TTSUsageMetricsData,
        )

        if isinstance(frame, TranscriptionFrame):
            self.db.add_utterance(
                self.call_id,
                "user",
                getattr(frame, "text", "") or "",
                source="stt",
                finalized=bool(getattr(frame, "finalized", False)),
            )
        elif isinstance(frame, InterimTranscriptionFrame):
            return
        elif isinstance(frame, LLMFullResponseStartFrame):
            self._llm_buf = []
            self._got_llm_turn = False
        elif isinstance(frame, LLMTextFrame):
            chunk = getattr(frame, "text", "") or ""
            if chunk:
                self._llm_buf.append(chunk)
        elif isinstance(frame, LLMFullResponseEndFrame):
            spoken = "".join(self._llm_buf).strip()
            self._llm_buf = []
            if spoken:
                self.db.add_utterance(self.call_id, "assistant", spoken, source="llm", finalized=True)
                self._got_llm_turn = True
            self._tts_buf = []
        elif isinstance(frame, TTSTextFrame):
            chunk = getattr(frame, "text", "") or ""
            if chunk.strip():
                self._tts_buf.append(chunk)
        elif isinstance(frame, FunctionCallInProgressFrame):
            tool_id = str(getattr(frame, "tool_call_id", "") or id(frame))
            name = getattr(frame, "function_name", "unknown")
            self._tool_starts[tool_id] = (name, time.perf_counter())
            self.db.add_event(self.call_id, "tool_start", {"name": name, "id": tool_id})
        elif isinstance(frame, FunctionCallResultFrame):
            tool_id = str(getattr(frame, "tool_call_id", "") or "")
            started = self._tool_starts.pop(tool_id, None)
            duration_ms = None
            if started:
                duration_ms = (time.perf_counter() - started[1]) * 1000.0
            self.db.add_tool(
                self.call_id,
                frame.function_name,
                frame.arguments,
                frame.result,
                duration_ms=duration_ms,
            )
        elif isinstance(frame, UserStartedSpeakingFrame):
            self.db.add_event(self.call_id, "user_started_speaking")
        elif isinstance(frame, UserStoppedSpeakingFrame):
            self.db.add_event(self.call_id, "user_stopped_speaking")
        elif isinstance(frame, BotStartedSpeakingFrame):
            self.db.add_event(self.call_id, "bot_started_speaking")
        elif isinstance(frame, BotStoppedSpeakingFrame):
            if not self._got_llm_turn and self._tts_buf:
                spoken = "".join(self._tts_buf).strip()
                if spoken:
                    self.db.add_utterance(
                        self.call_id, "assistant", spoken, source="tts", finalized=True
                    )
            self._tts_buf = []
            self._got_llm_turn = False
            self.db.add_event(self.call_id, "bot_stopped_speaking")
        elif isinstance(frame, InterruptionFrame):
            self.db.add_event(self.call_id, "interruption")
        elif isinstance(frame, MetricsFrame):
            self._ingest_metrics(frame.data or [])

    def _ingest_metrics(self, items) -> None:
        from pipecat.metrics.metrics import (
            LLMUsageMetricsData,
            ProcessingMetricsData,
            STTUsageMetricsData,
            TextAggregationMetricsData,
            TTFAMetricsData,
            TTFBMetricsData,
            TTSUsageMetricsData,
        )

        for item in items:
            if isinstance(item, TTFBMetricsData):
                self.db.add_metric(
                    self.call_id,
                    kind="ttfb",
                    processor=item.processor,
                    model=item.model,
                    ttfb_ms=float(item.value) * 1000.0,
                )
            elif isinstance(item, TTFAMetricsData):
                self.db.add_metric(
                    self.call_id,
                    kind="ttfa",
                    processor=item.processor,
                    model=item.model,
                    ttfb_ms=float(item.ttfb) * 1000.0,
                    processing_ms=float(item.ttfa) * 1000.0,
                    extra={"leading_silence_ms": float(item.leading_silence) * 1000.0},
                )
            elif isinstance(item, ProcessingMetricsData):
                self.db.add_metric(
                    self.call_id,
                    kind="processing",
                    processor=item.processor,
                    model=item.model,
                    processing_ms=float(item.value) * 1000.0,
                )
            elif isinstance(item, LLMUsageMetricsData):
                usage = item.value
                self.db.add_metric(
                    self.call_id,
                    kind="llm_tokens",
                    processor=item.processor,
                    model=item.model,
                    prompt_tokens=usage.prompt_tokens,
                    completion_tokens=usage.completion_tokens,
                    total_tokens=usage.total_tokens,
                    extra={
                        "reasoning_tokens": usage.reasoning_tokens,
                        "cache_read": usage.cache_read_input_tokens,
                    },
                )
            elif isinstance(item, STTUsageMetricsData):
                self.db.add_metric(
                    self.call_id,
                    kind="stt_audio",
                    processor=item.processor,
                    model=item.model,
                    extra={"audio_seconds": item.value.audio_seconds},
                )
            elif isinstance(item, TTSUsageMetricsData):
                self.db.add_metric(
                    self.call_id,
                    kind="tts_chars",
                    processor=item.processor,
                    model=item.model,
                    extra={"characters": item.value},
                )
            elif isinstance(item, TextAggregationMetricsData):
                self.db.add_metric(
                    self.call_id,
                    kind="text_aggregation",
                    processor=item.processor,
                    model=item.model,
                    processing_ms=float(item.value) * 1000.0,
                )
