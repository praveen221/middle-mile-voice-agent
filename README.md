# middle-mile-voice-agent

Open-source **multi-party voice agent** for middle-mile logistics negotiations.

It can:

1. Make outbound calls via **Exotel** (Vapi as a same-day PSTN fallback)
2. Speak and understand **Hinglish + Hindi**
3. Run **sequential** negotiations: driver → warehouse/customer → decide
4. Use tools (rate card, capacity, shipment status, shared state)
5. Iterate locally with real keys

Licensed under [MIT](LICENSE).

## Stack

| Layer | Default | Fallback |
| --- | --- | --- |
| Orchestration | [Pipecat](https://github.com/pipecat-ai/pipecat) (Python) | — |
| LLM | Gemini 2.5 Flash | — |
| STT | Sarvam `saaras:v3` | Deepgram |
| TTS | Sarvam `bulbul:v3` | Azure `hi-IN-SwaraNeural` |
| Local transport | Small WebRTC (browser mic) | Daily |
| Phone | Exotel Voicebot / flow | Vapi outbound |

The coordinator owns the goal, the current party, shared state, and the next action: stay on the call, dial the next party, reopen the previous party, escalate to a human, or close.

## Repo layout

```text
middle-mile-voice-agent/
├── src/
│   ├── config.py              # env + provider selection
│   ├── pipeline.py            # Pipecat STT → LLM → TTS
│   ├── agent/
│   │   ├── base_agent.py
│   │   ├── coordinator.py     # multi-party brain
│   │   ├── prompts.py         # spoken Hinglish
│   │   └── state.py           # session memory
│   ├── tools/
│   │   ├── rate_card.py
│   │   ├── capacity.py
│   │   ├── status.py
│   │   ├── negotiation.py
│   │   └── bindings.py        # Pipecat function-calling
│   └── telephony/
│       ├── exotel.py
│       └── vapi.py
├── scripts/
│   ├── run_local.py           # mic / browser, no phone
│   ├── run_outbound.py        # real Exotel outbound
│   ├── run_vapi.py            # same-day PSTN
│   └── test_tools.py
└── tests/
```

## Setup

Python 3.11+. 3.14 works for the tools/coordinator tests. The voice extras follow whatever Pipecat supports on your interpreter.

```bash
git clone https://github.com/praveen221/middle-mile-voice-agent.git
cd middle-mile-voice-agent
python3 -m venv .venv
source .venv/bin/activate

pip install -e ".[dev]"          # tools + tests
# when you are ready to talk:
pip install -e ".[voice]"
```

Or `pip install -r requirements.txt`.

```bash
cp .env.example .env
# fill GOOGLE_API_KEY plus SARVAM_API_KEY (or DEEPGRAM + AZURE)
```

`.env` is gitignored. Do not commit keys.

Minimum to hear the agent locally:

- `GOOGLE_API_KEY` — [Google AI Studio](https://aistudio.google.com/apikey)
- `SARVAM_API_KEY` — [Sarvam dashboard](https://dashboard.sarvam.ai/) (STT + TTS, Hinglish)

Deepgram + Azure Hindi TTS work if you skip Sarvam. Set `STT_PROVIDER` / `TTS_PROVIDER` accordingly.

## Phase 1 — local 1:1 (no phone)

```bash
python scripts/run_local.py
```

Pipecat prints a local URL. Open it, allow the mic, talk in Hinglish.

Demo shipment `MM-1001` is preloaded: BLR → HYD, 19ft, pickup 2026-08-14. Ask about rate or warehouse slots.

Daily instead of Small WebRTC:

```bash
python scripts/run_local.py --transport daily
```

Needs `DAILY_API_KEY`.

## Phase 2 — tools + state

```bash
python scripts/test_tools.py
pytest
```

Tools (swap the in-memory tables for your TMS later):

| Tool | What it does |
| --- | --- |
| `get_rate_card(origin, destination, vehicle_type)` | min / typical / max INR |
| `check_capacity(location, date)` | warehouse slots |
| `get_shipment_status(shipment_id)` | assignment + party numbers |
| `update_negotiation_state(...)` | patch shared memory |
| `end_party_call(...)` | close this party, ask coordinator what to do |

State is an in-memory dict keyed by `session_id`. Set `REDIS_URL` to persist across processes.

## Phase 3 — multi-party coordinator

`Coordinator` decides after every `end_party_call`:

| Action | When |
| --- | --- |
| `continue` | Current party still open |
| `call_next` | Current party accepted, next party pending |
| `call_previous` | Current party blocked/rejected, reopen earlier party |
| `escalate` | No previous party, handoff cap, or human flag |
| `complete` | Driver + warehouse + customer accepted |
| `hangup` | Nothing left to dial |

Default order: **driver → warehouse → customer**.

## Phase 4 — Exotel outbound

1. Create a Voicebot / flow applet in Exotel App Bazaar.
2. Point it at your Pipecat websocket (or SIP trunk).
3. Put `EXOTEL_*` values in `.env`.
4. Dry-run, then dial:

```bash
python scripts/run_outbound.py --shipment MM-1001 --dry-run
python scripts/run_outbound.py --to +9198XXXXXXXX --shipment MM-1001
```

The script places **one** outbound leg and tags `CustomField` with `session_id` + party. After that leg ends, read coordinator state and dial the next number. Wiring the hangup webhook to auto-dial is the remaining Exotel step.

## Vapi same-day path

If Exotel Voicebot is not live yet:

```bash
python scripts/run_vapi.py --to +9198XXXXXXXX --shipment MM-1001 --dry-run
python scripts/run_vapi.py --to +9198XXXXXXXX --shipment MM-1001
```

Needs `VAPI_API_KEY` and `VAPI_PHONE_NUMBER_ID`. Optional `VAPI_ASSISTANT_ID`; otherwise a transient assistant is created from this repo's Hinglish prompt.

## Phase 5 — evaluation

Record 20–30 real negotiations and score:

- Task completion
- Hinglish / Hindi accuracy
- Turns to resolution
- Cost per successful negotiation

## Demo data

| Shipment | Lane | Vehicle | Driver |
| --- | --- | --- | --- |
| `MM-1001` | BLR → HYD | 19ft | +919800000001 |
| `MM-1002` | DEL → MUM | 32ft | +919800000002 |
| `MM-1003` | BLR → CHN | 14ft | +919800000003 |

Rate cards live in `src/tools/rate_card.py`. Capacity lives in `src/tools/capacity.py`.

## Tests

```bash
pytest
```

Coordinator, tools, Exotel/Vapi clients, and config fallbacks run **without** Pipecat or API keys.
