# Voice-agent playground

This repository is the **public MIT voice lab**: STT → LLM → TTS, swap vendors, talk in the browser.

It is not a product workspace. Do not add company PRDs, investor decks, or claims/recovery code here.

## Run

```bash
python scripts/run_local.py        # playground :7860
python scripts/run_lab.py          # Lab UI :3000
pytest
```

Sample cases live in `src/scenarios/`. Replace them. Tools in `src/tools/` are in-memory fixtures.
