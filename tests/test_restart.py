import json
import os
import subprocess
import sys
from pathlib import Path

from agent_gate.engine import Engine
from agent_gate.errors import GateError
from agent_gate.models import DecisionIn

ROOT = Path(__file__).resolve().parents[1]


def _child(db: Path, dataset_uri: str, *args: str) -> dict:
    env = os.environ.copy()
    env["HL_DB_PATH"] = str(db)
    env["HL_DATASET_URI"] = dataset_uri
    env["HL_LLM_PROVIDER"] = "mock"
    env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    completed = subprocess.run(
        [sys.executable, str(ROOT / "tests" / "restart_child.py"), *args],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    return json.loads(completed.stdout)


def test_resume_after_process_restart(tmp_path: Path, dataset_uri: str):
    db = tmp_path / "gate.db"
    started = _child(db, dataset_uri, "start")
    assert started["status"] == "awaiting_approval"
    assert started["resume_cursor"] == "execute_tool"
    assert started["roles"] == ["system", "user", "assistant"]
    assert started["amount"] == "86.40"

    approved = _child(db, dataset_uri, "decide", started["run_id"], "approve")
    assert approved["status"] == "completed"
    assert approved["idempotent_replay"] is False
    assert approved["tool_execution_count"] == 1
    assert approved["final_answer"].startswith("Issued refund RF-")

    replay = _child(db, dataset_uri, "decide", started["run_id"], "approve")
    assert replay["idempotent_replay"] is True
    assert replay["tool_execution_count"] == 1
    assert replay["final_answer"] == approved["final_answer"]


def test_recover_finishes_a_claimed_gate_once(tmp_path: Path, dataset_uri: str, clock):
    db = tmp_path / "gate.db"
    engine = Engine(db_path=db, dataset_uri=dataset_uri, llm_provider="mock", clock=clock)
    view = engine.start("refund-stalled")

    def crash(run_id: str, origin: str | None = None):
        del run_id, origin
        raise GateError(500, "crash", "worker died after the claim")

    engine._execute = crash  # type: ignore[method-assign]
    try:
        engine.decide(DecisionIn(decision="approve", actor="ops.reviewer"), run_id=view.run_id)
    except GateError as exc:
        assert exc.code == "crash"
    assert engine.get(view.run_id).status == "executing"
    assert engine.get(view.run_id).tool_execution_count == 0

    revived = Engine(db_path=db, dataset_uri=dataset_uri, llm_provider="mock", clock=clock)
    assert revived.recover() == 1
    done = revived.get(view.run_id)
    assert done.status == "completed"
    assert done.tool_execution_count == 1
    assert revived.recover() == 0
