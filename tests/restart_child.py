"""One-shot process used by the restart test. Not a pytest module."""

from __future__ import annotations

import json
import os
import sys

from agent_gate.engine import Engine
from agent_gate.models import DecisionIn


def main() -> None:
    engine = Engine(
        db_path=os.environ["HL_DB_PATH"],
        dataset_uri=os.environ["HL_DATASET_URI"],
        llm_provider="mock",
    )
    command = sys.argv[1]
    if command == "start":
        view = engine.start("refund-stalled")
        assert view.gate is not None and view.pending_call is not None
        payload = {
            "run_id": view.run_id,
            "status": view.status,
            "gate_id": view.gate.gate_id,
            "resume_cursor": view.resume_cursor,
            "roles": [message.role for message in view.messages],
            "amount": view.pending_call.arguments["amount_usd"],
        }
    elif command == "decide":
        run_id, decision = sys.argv[2], sys.argv[3]
        reason = None if decision != "deny" else "Not now, thanks."
        result = engine.decide(
            DecisionIn(decision=decision, actor="ops.reviewer", reason=reason),
            run_id=run_id,
        )
        payload = {
            "status": result.run.status,
            "code": result.code,
            "idempotent_replay": result.idempotent_replay,
            "tool_execution_count": result.run.tool_execution_count,
            "final_answer": result.run.final_answer,
        }
    else:
        raise SystemExit(f"unknown command {command}")
    json.dump(payload, sys.stdout)


if __name__ == "__main__":
    main()
