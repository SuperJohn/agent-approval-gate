"""SQLite durability for runs, gates, the audit log, and one effect per gate."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from agent_gate.models import AgentState

SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_meta (
  version INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS runs (
  run_id TEXT PRIMARY KEY,
  scenario_id TEXT NOT NULL,
  status TEXT NOT NULL,
  state_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS gates (
  gate_id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL UNIQUE REFERENCES runs(run_id),
  tool_name TEXT NOT NULL,
  arguments_json TEXT NOT NULL,
  proposed_json TEXT NOT NULL,
  status TEXT NOT NULL,
  expires_at TEXT NOT NULL,
  decision_json TEXT,
  execution_json TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS effects (
  effect_id TEXT PRIMARY KEY,
  gate_id TEXT NOT NULL UNIQUE REFERENCES gates(gate_id),
  tool_name TEXT NOT NULL,
  result_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id TEXT NOT NULL REFERENCES runs(run_id),
  gate_id TEXT,
  ts TEXT NOT NULL,
  actor TEXT NOT NULL,
  event TEXT NOT NULL,
  detail_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_audit_run ON audit_log(run_id, id);
CREATE INDEX IF NOT EXISTS idx_runs_status ON runs(status);
"""


def dumps(payload: object) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


class Store:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._migrate()

    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.path, isolation_level=None, timeout=5)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys=ON")
        con.execute("PRAGMA busy_timeout=5000")
        con.execute("PRAGMA journal_mode=WAL")
        return con

    def _migrate(self) -> None:
        con = self._connect()
        try:
            con.executescript(SCHEMA)
            row = con.execute("SELECT version FROM schema_meta LIMIT 1").fetchone()
            if row is None:
                con.execute("INSERT INTO schema_meta (version) VALUES (1)")
        finally:
            con.close()

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        con = self._connect()
        try:
            con.execute("BEGIN IMMEDIATE")
            yield con
        except Exception:
            con.execute("ROLLBACK")
            raise
        else:
            con.execute("COMMIT")
        finally:
            con.close()

    def query(self, fn: Callable[[sqlite3.Connection], Any]) -> Any:
        con = self._connect()
        try:
            return fn(con)
        finally:
            con.close()

    def backup_to(self, dest: Path) -> None:
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            dest.unlink()
        src = self._connect()
        dst = sqlite3.connect(dest)
        try:
            src.backup(dst)
        finally:
            dst.close()
            src.close()

    def insert_run(self, con: sqlite3.Connection, state: AgentState) -> None:
        con.execute(
            """
            INSERT INTO runs (run_id, scenario_id, status, state_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                state.run_id,
                state.scenario_id,
                state.status,
                dumps(state.model_dump(mode="json")),
                state.created_at,
                state.updated_at,
            ),
        )

    def save_state(self, con: sqlite3.Connection, state: AgentState) -> None:
        con.execute(
            """
            UPDATE runs
            SET status = ?, state_json = ?, updated_at = ?
            WHERE run_id = ?
            """,
            (
                state.status,
                dumps(state.model_dump(mode="json")),
                state.updated_at,
                state.run_id,
            ),
        )

    def insert_gate(
        self,
        con: sqlite3.Connection,
        *,
        gate_id: str,
        run_id: str,
        tool_name: str,
        arguments: dict[str, Any],
        expires_at: str,
        now: str,
    ) -> None:
        blob = dumps(arguments)
        con.execute(
            """
            INSERT INTO gates (
              gate_id, run_id, tool_name, arguments_json, proposed_json,
              status, expires_at, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, 'open', ?, ?, ?)
            """,
            (gate_id, run_id, tool_name, blob, blob, expires_at, now, now),
        )

    def insert_effect(
        self,
        con: sqlite3.Connection,
        *,
        effect_id: str,
        gate_id: str,
        tool_name: str,
        result: dict[str, Any],
        now: str,
    ) -> None:
        con.execute(
            """
            INSERT INTO effects (effect_id, gate_id, tool_name, result_json, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (effect_id, gate_id, tool_name, dumps(result), now),
        )

    def add_audit(
        self,
        con: sqlite3.Connection,
        *,
        run_id: str,
        gate_id: str | None,
        ts: str,
        actor: str,
        event: str,
        detail: dict[str, Any],
    ) -> None:
        con.execute(
            """
            INSERT INTO audit_log (run_id, gate_id, ts, actor, event, detail_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (run_id, gate_id, ts, actor, event, dumps(detail)),
        )

    @staticmethod
    def load_state(row: sqlite3.Row) -> AgentState:
        return AgentState.model_validate(json.loads(row["state_json"]))

    @staticmethod
    def get_run(con: sqlite3.Connection, run_id: str) -> sqlite3.Row | None:
        return con.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,)).fetchone()

    @staticmethod
    def get_gate(con: sqlite3.Connection, gate_id: str) -> sqlite3.Row | None:
        return con.execute("SELECT * FROM gates WHERE gate_id = ?", (gate_id,)).fetchone()

    @staticmethod
    def get_gate_for_run(con: sqlite3.Connection, run_id: str) -> sqlite3.Row | None:
        return con.execute("SELECT * FROM gates WHERE run_id = ?", (run_id,)).fetchone()

    @staticmethod
    def audit_rows(con: sqlite3.Connection, run_id: str) -> list[sqlite3.Row]:
        return list(
            con.execute(
                "SELECT * FROM audit_log WHERE run_id = ? ORDER BY id",
                (run_id,),
            )
        )

    def list_run_ids(self, status: str) -> list[str]:
        def read(con: sqlite3.Connection) -> list[str]:
            rows = con.execute(
                "SELECT run_id FROM runs WHERE status = ? ORDER BY created_at, run_id",
                (status,),
            )
            return [row[0] for row in rows]

        return self.query(read)
