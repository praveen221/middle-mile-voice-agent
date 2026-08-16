#!/usr/bin/env python3
"""Print the last recorded call from SQLite."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.eval.db import CallDB
from src.eval.seed import seed_kimi_baseline


def main() -> int:
    db = CallDB()
    seed_kimi_baseline(db)
    last = db.last_call()
    if last is None:
        print("No calls recorded yet.")
        return 1
    summary = db.call_summary(int(last["id"]))
    call = summary["call"]
    print(f"call_id={call['id']} {call['started_at']} → {call['ended_at']}")
    print(f"situation={call.get('situation_title')}  tester={call.get('tester_name')}")
    print(f"llm={call['llm_provider']}/{call['llm_model']}  party={call['party']}  status={call['status']}")
    if call.get("transcript"):
        print("\n--- transcript ---")
        print(call["transcript"])
    print(f"tokens={summary['tokens']}  user_to_bot={summary['user_to_bot']}")
    print(f"db={db.path}")
    if summary["ttfb_by_processor"]:
        print("\n--- ttfb ---")
        for row in summary["ttfb_by_processor"]:
            print(f"  {row['processor']}: avg={row['avg_ms']:.0f}ms max={row['max_ms']:.0f}ms n={row['n']}")
    print("\n--- utterances ---")
    for row in summary["utterances"]:
        src = row.get("source") or ""
        print(f"[{row['role']}/{src}] {row['text'][:500]}")
    print("\n--- tools ---")
    for row in summary["tools"]:
        dur = row.get("duration_ms")
        print(f"{row['name']} {dur:.0f}ms" if dur else row["name"])
        print(f"  args={str(row['arguments'])[:240]}")
        print(f"  result={str(row['result'])[:240]}")
    print("\n--- events ---")
    for row in summary["events"][-30:]:
        print(f"  {row['ts']}  {row['name']}  {row.get('detail') or ''}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
