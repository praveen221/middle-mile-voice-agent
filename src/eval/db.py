"""SQLite log of every call: prompt, transcript, tools, metrics, events."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
from datetime import UTC, datetime
from pathlib import Path

DEFAULT_DB = Path(".local/calls.db")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS calls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    ended_at TEXT,
    session_id TEXT,
    party TEXT,
    scenario_id TEXT,
    llm_provider TEXT,
    llm_model TEXT,
    stt TEXT,
    tts TEXT,
    status TEXT,
    prompt TEXT,
    snapshot_json TEXT,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS utterances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    call_id INTEGER NOT NULL,
    ts TEXT NOT NULL,
    role TEXT NOT NULL,
    text TEXT NOT NULL,
    source TEXT,
    finalized INTEGER,
    FOREIGN KEY (call_id) REFERENCES calls(id)
);

CREATE TABLE IF NOT EXISTS tools (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    call_id INTEGER NOT NULL,
    ts TEXT NOT NULL,
    name TEXT NOT NULL,
    arguments TEXT,
    result TEXT,
    duration_ms REAL,
    FOREIGN KEY (call_id) REFERENCES calls(id)
);

CREATE TABLE IF NOT EXISTS metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    call_id INTEGER NOT NULL,
    ts TEXT NOT NULL,
    kind TEXT NOT NULL,
    processor TEXT,
    model TEXT,
    ttfb_ms REAL,
    processing_ms REAL,
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_tokens INTEGER,
    extra_json TEXT,
    FOREIGN KEY (call_id) REFERENCES calls(id)
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    call_id INTEGER NOT NULL,
    ts TEXT NOT NULL,
    name TEXT NOT NULL,
    detail TEXT,
    FOREIGN KEY (call_id) REFERENCES calls(id)
);

CREATE TABLE IF NOT EXISTS configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    fingerprint TEXT NOT NULL UNIQUE,
    stt TEXT,
    stt_language TEXT,
    tts TEXT,
    tts_language TEXT,
    tts_voice TEXT,
    llm_provider TEXT,
    llm_model TEXT,
    situation_id TEXT,
    situation_title TEXT,
    stack_json TEXT NOT NULL,
    situation_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT
);
"""


def _now() -> str:
    return datetime.now(UTC).isoformat()


class CallDB:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or Path(__file__).resolve().parents[2] / DEFAULT_DB
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        with self._lock:
            self._conn.executescript(_SCHEMA)
            self._migrate()
            self._conn.commit()

    def _migrate(self) -> None:
        utt_cols = {r[1] for r in self._conn.execute("PRAGMA table_info(utterances)")}
        if "source" not in utt_cols:
            self._conn.execute("ALTER TABLE utterances ADD COLUMN source TEXT")
        if "finalized" not in utt_cols:
            self._conn.execute("ALTER TABLE utterances ADD COLUMN finalized INTEGER")
        tool_cols = {r[1] for r in self._conn.execute("PRAGMA table_info(tools)")}
        if "duration_ms" not in tool_cols:
            self._conn.execute("ALTER TABLE tools ADD COLUMN duration_ms REAL")
        call_cols = {r[1] for r in self._conn.execute("PRAGMA table_info(calls)")}
        for name, spec in (
            ("situation_title", "TEXT"),
            ("situation_json", "TEXT"),
            ("tester_name", "TEXT"),
            ("transcript", "TEXT"),
            ("config_id", "INTEGER"),
        ):
            if name not in call_cols:
                self._conn.execute(f"ALTER TABLE calls ADD COLUMN {name} {spec}")

    def start_call(
        self,
        *,
        session_id: str,
        party: str,
        scenario_id: str | None,
        llm_provider: str,
        llm_model: str,
        stt: str,
        tts: str,
        prompt: str,
        snapshot: str | None = None,
        notes: str | None = None,
        started_at: str | None = None,
        situation_title: str | None = None,
        situation_json: str | None = None,
        tester_name: str | None = None,
        transcript: str | None = None,
        config_id: int | None = None,
    ) -> int:
        with self._lock:
            cur = self._conn.execute(
                """
                INSERT INTO calls (
                    started_at, session_id, party, scenario_id,
                    llm_provider, llm_model, stt, tts, status, prompt,
                    snapshot_json, notes, situation_title, situation_json,
                    tester_name, transcript, config_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'open', ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    started_at or _now(),
                    session_id,
                    party,
                    scenario_id,
                    llm_provider,
                    llm_model,
                    stt,
                    tts,
                    prompt,
                    snapshot,
                    notes,
                    situation_title,
                    situation_json,
                    tester_name,
                    transcript,
                    config_id,
                ),
            )
            self._conn.commit()
            return int(cur.lastrowid)

    def end_call(
        self,
        call_id: int,
        *,
        status: str,
        snapshot: str | None = None,
        transcript: str | None = None,
    ) -> None:
        if transcript is None:
            transcript = self.compose_transcript(call_id)
        with self._lock:
            self._conn.execute(
                """
                UPDATE calls
                SET ended_at = ?, status = ?,
                    snapshot_json = COALESCE(?, snapshot_json),
                    transcript = COALESCE(?, transcript)
                WHERE id = ?
                """,
                (_now(), status, snapshot, transcript, call_id),
            )
            self._conn.commit()

    def compose_transcript(self, call_id: int) -> str:
        with self._lock:
            rows = self._conn.execute(
                """
                SELECT role, text, source, finalized
                FROM utterances
                WHERE call_id = ?
                ORDER BY id
                """,
                (call_id,),
            ).fetchall()
        lines: list[str] = []
        for row in rows:
            source = row["source"] or ""
            if source == "stt_interim":
                continue
            if row["role"] == "user" and source in ("", "stt"):
                lines.append(f"USER: {row['text']}")
            elif row["role"] == "assistant" and source in ("", "llm", "tts"):
                lines.append(f"AGENT: {row['text']}")
        return "\n".join(lines)

    def add_utterance(
        self,
        call_id: int,
        role: str,
        text: str,
        *,
        source: str | None = None,
        finalized: bool | None = None,
    ) -> None:
        text = (text or "").strip()
        if not text:
            return
        with self._lock:
            if role == "user" and source == "stt":
                last = self._conn.execute(
                    """
                    SELECT id, text FROM utterances
                    WHERE call_id = ? AND role = 'user' AND source = 'stt'
                    ORDER BY id DESC LIMIT 1
                    """,
                    (call_id,),
                ).fetchone()
                if last:
                    prev = last["text"]
                    if text.startswith(prev) or prev.startswith(text):
                        self._conn.execute(
                            """
                            UPDATE utterances SET ts = ?, text = ?, finalized = ?
                            WHERE id = ?
                            """,
                            (_now(), text, int(bool(finalized)) if finalized is not None else None, last["id"]),
                        )
                        self._conn.commit()
                        return
            self._conn.execute(
                """
                INSERT INTO utterances (call_id, ts, role, text, source, finalized)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    call_id,
                    _now(),
                    role,
                    text,
                    source,
                    int(bool(finalized)) if finalized is not None else None,
                ),
            )
            self._conn.commit()

    def add_tool(
        self,
        call_id: int,
        name: str,
        arguments: object,
        result: object,
        *,
        duration_ms: float | None = None,
    ) -> None:
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO tools (call_id, ts, name, arguments, result, duration_ms)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    call_id,
                    _now(),
                    name,
                    json.dumps(arguments, default=str),
                    json.dumps(result, default=str),
                    duration_ms,
                ),
            )
            self._conn.commit()

    def add_metric(
        self,
        call_id: int,
        *,
        kind: str,
        processor: str | None = None,
        model: str | None = None,
        ttfb_ms: float | None = None,
        processing_ms: float | None = None,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        total_tokens: int | None = None,
        extra: object | None = None,
    ) -> None:
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO metrics (
                    call_id, ts, kind, processor, model, ttfb_ms, processing_ms,
                    prompt_tokens, completion_tokens, total_tokens, extra_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    call_id,
                    _now(),
                    kind,
                    processor,
                    model,
                    ttfb_ms,
                    processing_ms,
                    prompt_tokens,
                    completion_tokens,
                    total_tokens,
                    json.dumps(extra, default=str) if extra is not None else None,
                ),
            )
            self._conn.commit()

    def add_event(self, call_id: int, name: str, detail: object | None = None) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO events (call_id, ts, name, detail) VALUES (?, ?, ?, ?)",
                (
                    call_id,
                    _now(),
                    name,
                    json.dumps(detail, default=str) if detail is not None else None,
                ),
            )
            self._conn.commit()

    def last_call(self) -> sqlite3.Row | None:
        with self._lock:
            return self._conn.execute("SELECT * FROM calls ORDER BY id DESC LIMIT 1").fetchone()

    def call_summary(self, call_id: int) -> dict:
        with self._lock:
            call = self._conn.execute("SELECT * FROM calls WHERE id = ?", (call_id,)).fetchone()
            utts = self._conn.execute(
                "SELECT role, text, ts, source, finalized FROM utterances WHERE call_id = ? ORDER BY id",
                (call_id,),
            ).fetchall()
            tools = self._conn.execute(
                "SELECT name, arguments, result, duration_ms, ts FROM tools WHERE call_id = ? ORDER BY id",
                (call_id,),
            ).fetchall()
            events = self._conn.execute(
                "SELECT name, detail, ts FROM events WHERE call_id = ? ORDER BY id",
                (call_id,),
            ).fetchall()
            tokens = self._conn.execute(
                """
                SELECT
                    COALESCE(SUM(prompt_tokens), 0),
                    COALESCE(SUM(completion_tokens), 0),
                    COALESCE(SUM(total_tokens), 0)
                FROM metrics WHERE call_id = ? AND kind = 'llm_tokens'
                """,
                (call_id,),
            ).fetchone()
            ttfb = self._conn.execute(
                """
                SELECT processor, AVG(ttfb_ms), MAX(ttfb_ms), COUNT(*)
                FROM metrics WHERE call_id = ? AND kind = 'ttfb' AND ttfb_ms IS NOT NULL
                GROUP BY processor
                """,
                (call_id,),
            ).fetchall()
            turns = self._conn.execute(
                """
                SELECT AVG(processing_ms), MAX(processing_ms), COUNT(*)
                FROM metrics WHERE call_id = ? AND kind = 'user_to_bot'
                """,
                (call_id,),
            ).fetchone()
        return {
            "call": dict(call) if call else None,
            "utterances": [dict(r) for r in utts],
            "tools": [dict(r) for r in tools],
            "events": [dict(r) for r in events],
            "tokens": {
                "prompt": tokens[0] if tokens else 0,
                "completion": tokens[1] if tokens else 0,
                "total": tokens[2] if tokens else 0,
            },
            "ttfb_by_processor": [
                {"processor": r[0], "avg_ms": r[1], "max_ms": r[2], "n": r[3]} for r in ttfb
            ],
            "user_to_bot": {
                "avg_ms": turns[0] if turns else None,
                "max_ms": turns[1] if turns else None,
                "n": turns[2] if turns else 0,
            },
        }

    def has_notes(self, notes: str) -> bool:
        with self._lock:
            row = self._conn.execute(
                "SELECT 1 FROM calls WHERE notes = ? LIMIT 1", (notes,)
            ).fetchone()
        return row is not None

    def set_meta(self, key: str, value: str | None) -> None:
        with self._lock:
            if value is None:
                self._conn.execute("DELETE FROM meta WHERE key = ?", (key,))
            else:
                self._conn.execute(
                    "INSERT INTO meta(key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                    (key, value),
                )
            self._conn.commit()

    def get_meta(self, key: str) -> str | None:
        with self._lock:
            row = self._conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
        return None if row is None else row["value"]

    def save_config(
        self,
        *,
        stack: dict,
        situation: dict,
        fingerprint: str | None = None,
    ) -> dict:
        """Insert a stack+situation snapshot, or reuse the same fingerprint."""
        sit = dict(situation)
        sit.pop("tester_name", None)
        payload = {"stack": stack, "situation": sit}
        fp = fingerprint or hashlib.sha256(
            json.dumps(payload, sort_keys=True, default=str).encode()
        ).hexdigest()[:16]
        with self._lock:
            existing = self._conn.execute(
                "SELECT * FROM configs WHERE fingerprint = ?", (fp,)
            ).fetchone()
            if existing is None:
                cur = self._conn.execute(
                    """
                    INSERT INTO configs (
                        created_at, fingerprint, stt, stt_language, tts, tts_language,
                        tts_voice, llm_provider, llm_model, situation_id, situation_title,
                        stack_json, situation_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        _now(),
                        fp,
                        stack.get("stt"),
                        stack.get("stt_language"),
                        stack.get("tts"),
                        stack.get("tts_language"),
                        stack.get("tts_voice"),
                        stack.get("llm_provider"),
                        stack.get("llm_model"),
                        sit.get("id"),
                        sit.get("title"),
                        json.dumps(stack, default=str),
                        json.dumps(situation, default=str),
                    ),
                )
                self._conn.commit()
                config_id = int(cur.lastrowid)
                reused = False
            else:
                config_id = int(existing["id"])
                reused = True
        self.set_meta("active_config_id", str(config_id))
        row = self.get_config(config_id)
        assert row is not None
        row["reused"] = reused
        return row

    def active_config_id(self) -> int | None:
        raw = self.get_meta("active_config_id")
        if not raw:
            return None
        try:
            return int(raw)
        except ValueError:
            return None

    def get_config(self, config_id: int) -> dict | None:
        with self._lock:
            row = self._conn.execute("SELECT * FROM configs WHERE id = ?", (config_id,)).fetchone()
            if row is None:
                return None
            n = self._conn.execute(
                "SELECT COUNT(*) FROM calls WHERE config_id = ?", (config_id,)
            ).fetchone()[0]
        out = dict(row)
        out["call_count"] = int(n)
        return out

    def list_configs(self, limit: int = 40) -> list[dict]:
        with self._lock:
            rows = self._conn.execute(
                """
                SELECT c.*, COALESCE(x.n, 0) AS call_count
                FROM configs c
                LEFT JOIN (
                    SELECT config_id, COUNT(*) AS n FROM calls GROUP BY config_id
                ) x ON x.config_id = c.id
                ORDER BY c.id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]

    def list_calls(self, *, config_id: int | None = None, limit: int = 40) -> list[dict]:
        with self._lock:
            if config_id is None:
                rows = self._conn.execute(
                    """
                    SELECT id, started_at, ended_at, status, tester_name, situation_title,
                           llm_model, stt, tts, config_id, transcript
                    FROM calls
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()
            else:
                rows = self._conn.execute(
                    """
                    SELECT id, started_at, ended_at, status, tester_name, situation_title,
                           llm_model, stt, tts, config_id, transcript
                    FROM calls
                    WHERE config_id = ?
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (config_id, limit),
                ).fetchall()
        out = []
        for row in rows:
            item = dict(row)
            text = item.get("transcript") or ""
            item["preview"] = text[:240]
            out.append(item)
        return out

