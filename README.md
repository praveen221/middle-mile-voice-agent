# middle-mile-voice-agent

Open-source **multi-party voice agent** for middle-mile logistics negotiations.

Licensed under [MIT](LICENSE).

## What “run it locally” actually does

It does **not** call your phone.

You start a voice loop in the browser. The agent speaks first, as if it just
dialled you. You are not the company. You play the other party — by default
**Ramesh, the driver** — and you push a real desk problem at it.

That is the first baseline: Gemini + Sarvam (or Deepgram/Azure) + this
coordinator, on one hard conversation. The first attempt will be rough. The
point is to hear *where* it breaks: language, invented numbers, folding on
rate, or never closing.

```bash
cp .env.example .env          # GOOGLE_API_KEY + SARVAM_API_KEY
pip install -e ".[voice]"
python scripts/run_local.py --brief     # read the case, no mic
python scripts/run_local.py             # browser mic; agent greets first
```

Allow the microphone. Wait. Answer like a driver. Close the tab when a real
person would hang up. The terminal prints a scorecard.

Then play the next party against the same saved state:

```bash
python scripts/run_local.py --party warehouse
python scripts/run_local.py --party customer
python scripts/run_local.py --fresh     # wipe and start the case over
```

A real three-phone sequential outbound (Exotel / Vapi) is a later test. Local
is one human, one party, one call, on purpose.

## The case you are playing

**Same-day Whitefield → Patancheru** (`MM-1001`). Composite of a desk failure
that shows up on Amazon/Flipkart inbound appointments and FMCG DC slots
every diesel spike and festive rush.

| Fact | Value |
| --- | --- |
| Clock | Thu 14 Aug 2026, 8:35am IST |
| Load | 19ft, 8 pallets, Whitefield 3PL → Northstar Foods DC, Patancheru |
| Tonight's DC window | 8pm–10pm. Next receiving: Saturday |
| Must gate-out Whitefield | 12:00 or the appointment dies |
| Reserved dock | 10:30–11:30, released at noon |
| Contracted last night | ₹21,000 |
| Rate card | min ₹18k / typical ₹21k / **max ₹24k** |
| Driver (you) | Ramesh, Electronic City, wants **₹28,000** this morning |
| Miss cost (internal) | OTIF fail + ₹15,000. Agent must not dump this number at the driver |

**You (driver):** hold ₹28k. If the agent is specific and respectful and offers
at or under ₹24k with a real 10:30 dock, you may settle ~₹23–24k and give a
10:15 Whitefield ETA. If it sounds like a chatbot or invents a rate, hold or
hang up.

**The agent must:** look up the rate card before quoting, stay at or under
₹24k or escalate, not invent slots, get a rate and an arrival time, then close.

Automatic checks after the call: did it use the rate card, did it close the
party, did it accept above the cap. Language and “would a real driver stay”
you score by ear.

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
│   ├── scenarios/             # eval case files + playbooks
│   ├── eval/                  # debrief + local session save
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

- `OPENROUTER_API_KEY` — [OpenRouter](https://openrouter.ai/keys) (swap models via `LLM_MODEL`)
- `SARVAM_API_KEY` — [Sarvam dashboard](https://dashboard.sarvam.ai/) → **Sarvam API** (STT + TTS)

`GOOGLE_API_KEY` is only needed if you skip OpenRouter.

Deepgram + Azure Hindi TTS work if you skip Sarvam. Set `STT_PROVIDER` / `TTS_PROVIDER` accordingly.

## Phase 1 — local 1:1 (no phone)

Covered above. Daily instead of Small WebRTC:

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

First: run the Whitefield case 5–10 times as the driver. Write down, per run:

- Auto pass / fail from the terminal scorecard
- Hinglish: could you stay in mixed Hindi-English without the agent snapping to English
- Constraint: did it go over ₹24k, invent a slot, or leak the penalty
- Close: did it end the call or wander
- Feel: would a real driver stay

Then warehouse, then customer, using the saved session so the agent has to
carry the rate it already “agreed”.

Later, on real phones, record 20–30 live negotiations and add cost per success.

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
