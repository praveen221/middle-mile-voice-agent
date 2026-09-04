# middle-mile-voice-agent

Open-source **voice-agent playground**. Swap STT, LLM, and TTS, then talk to a multi-party agent in the browser. MIT licensed.

This repo is a lab, not a product. Use it to try live speech pipelines with the models you want. The bundled case is a replaceable sample booking, not a real desk.

## What “run it locally” actually does

It does **not** call your phone.

You start a voice loop in the browser. The agent speaks first, as if it just dialled you. You play the other party. Pick STT / LLM / TTS in the Lab, or leave the defaults.

```bash
cp .env.example .env          # OPENROUTER_API_KEY + SARVAM_API_KEY (or other vendors)
pip install -e ".[voice]"
python scripts/run_local.py --brief     # read the sample case, no mic
python scripts/run_local.py             # browser mic; agent greets first
```

Allow the microphone. Wait. Answer. Close the tab when a real person would hang up. The terminal prints a scorecard.

Lab UI (dropdowns + editable situation) in a second terminal:

```bash
python scripts/run_lab.py             # http://localhost:3000
# playground must also be running: python scripts/run_local.py
```

Then play the next party against the same saved state:

```bash
python scripts/run_local.py --party venue
python scripts/run_local.py --party client
python scripts/run_local.py --fresh     # wipe and start the case over
```

A real phone outbound (Exotel / Vapi) is optional and later.

## The sample case

**Sample: 4pm session, vendor wants more** (`BK-1001`). A generic three-party booking so you have something to talk to. Replace it.

| Fact | Value |
| --- | --- |
| Clock | Frozen at Thu 14 Aug 2026, 2:10pm (tools stay deterministic) |
| Item | half-day, Andheri → Bandra |
| Window | 4pm–6pm. Next opening: tomorrow |
| Contracted last night | ₹8,000 |
| Catalog | min ₹7k / typical ₹8k / **max ₹10k** |
| Vendor (you) | Asha, wants **₹12,000** this morning |

**You (vendor):** hold ₹12k. If the agent is specific and respectful and offers at or under ₹10k with a real 4pm start, you may settle ~₹9–10k. If it sounds like a chatbot or invents a number, hold or hang up.

**The agent must:** look up the catalog before quoting, stay at or under ₹10k or escalate, not invent slots, get a price and an arrival time, then close.

Automatic checks after the call: did it use the catalog, did it close the party, did it accept above the cap. Language you score by ear.

Swap the case in `src/scenarios/` or in the Lab situation panel.

## Stack

| Layer | Default | Fallback |
| --- | --- | --- |
| Orchestration | [Pipecat](https://github.com/pipecat-ai/pipecat) (Python) | — |
| LLM | OpenRouter (set `LLM_MODEL`) | Sarvam / Gemini |
| STT | Sarvam `saaras:v3` | Deepgram / Azure / Cartesia / Smallest |
| TTS | Sarvam `bulbul:v3` | Azure / Deepgram / Cartesia / Smallest |
| Local transport | Small WebRTC (browser mic) | Daily |
| Phone | Exotel Voicebot / flow | Vapi outbound |

The coordinator owns the goal, the current party, shared state, and the next action: stay on the call, dial the next party, reopen the previous party, escalate to a human, or close.

## Repo layout

```text
middle-mile-voice-agent/
├── src/
│   ├── config.py              # env + provider selection
│   ├── pipeline.py            # Pipecat STT → LLM → TTS
│   ├── agent/                 # coordinator, prompts, session memory
│   ├── scenarios/             # sample cases — replace these
│   ├── eval/                  # debrief + local session save
│   ├── lab/                   # Lab catalog, stack, situation
│   ├── tools/                 # sample catalog / availability / records
│   └── telephony/             # Exotel, Vapi
├── scripts/
│   ├── run_local.py           # mic / browser, no phone
│   ├── run_lab.py             # Lab UI on :3000
│   ├── run_outbound.py        # real Exotel outbound
│   └── run_vapi.py            # PSTN via Vapi
├── web/lab.html               # Lab UI
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
# fill OPENROUTER_API_KEY plus SARVAM_API_KEY (or DEEPGRAM + AZURE)
```

`.env` is gitignored. Do not commit keys.

Minimum to hear the agent locally:

- `OPENROUTER_API_KEY` — [OpenRouter](https://openrouter.ai/keys) (swap models via `LLM_MODEL`)
- `SARVAM_API_KEY` — [Sarvam dashboard](https://dashboard.sarvam.ai/) → **Sarvam API** (STT + TTS)

`GOOGLE_API_KEY` is only needed if you skip OpenRouter.

## Tools

Sample in-memory tables. Swap them for your own.

| Tool | What it does |
| --- | --- |
| `lookup_price(origin, destination, item_type)` | min / typical / max |
| `check_availability(location, date)` | slots at a place |
| `get_record_status(record_id)` | assignment + party numbers |
| `update_negotiation_state(...)` | patch shared memory |
| `end_party_call(...)` | close this party, ask coordinator what to do |

Default party order: **vendor → venue → client**.

## Tests

```bash
pytest
```

Coordinator, tools, Exotel/Vapi clients, and config fallbacks run **without** Pipecat or API keys.

Licensed under [MIT](LICENSE).
