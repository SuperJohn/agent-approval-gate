"""Record the synthetic scenarios into site/data for the static replay.

The clock is frozen, and ids come from the scenario id, so the JSON is stable.
"""

from __future__ import annotations

import json
import tempfile
from datetime import timedelta
from pathlib import Path

from agent_gate.clock import ManualClock, iso, parse_iso
from agent_gate.dataset import Dataset, load_dataset
from agent_gate.engine import Engine, StableIds
from agent_gate.errors import GateError
from agent_gate.llm import MockProvider
from agent_gate.models import DecisionIn, RunView, Scenario
from agent_gate.store import Store
from agent_gate.tools import ToolRegistry, summarize_result

RECORD_START_ISO = "2026-10-28T15:00:00Z"
ACTOR = "ops.reviewer"
ROOT = Path(__file__).resolve().parents[1]


def build_bundle(dataset_uri: str | None = None) -> dict:
    dataset = load_dataset(dataset_uri)
    tools = ToolRegistry(dataset)
    runs = [_record_one(dataset, tools, scenario) for scenario in dataset.scenarios.values()]
    return {
        "product": "agent-approval-gate",
        "org": "Houghton Labs",
        "generated_at": RECORD_START_ISO,
        "clock": "frozen",
        "provider": "mock",
        "note": (
            "Synthetic recording of Northwind Field Goods. "
            "This page replays these branches and does not call a server."
        ),
        "runs": runs,
    }


def write_bundle(bundle: dict, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(bundle, indent=2) + "\n"
    (dest / "runs.json").write_text(payload, encoding="utf-8")
    script = "window.HL_RUNS = " + json.dumps(bundle, indent=2).replace("<", "\\u003c") + ";\n"
    (dest / "runs.js").write_text(script, encoding="utf-8")


def main() -> None:
    bundle = build_bundle()
    write_bundle(bundle, ROOT / "site" / "data")
    print(f"wrote {len(bundle['runs'])} runs to site/data")


def _record_one(dataset: Dataset, tools: ToolRegistry, scenario: Scenario) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        paused_path = root / "paused.sqlite"
        paused = _engine(paused_path, dataset)
        view = paused.start(scenario.id)
        assert view.gate is not None
        state_blob, state_bytes = _state_blob(paused, view.run_id)
        pause_id = view.audit[-1].id
        approve = _branch(
            paused,
            root / "approve.sqlite",
            dataset,
            lambda engine, clock: _approve(engine, clock, scenario, view.run_id),
        )
        deny = _branch(
            paused,
            root / "deny.sqlite",
            dataset,
            lambda engine, clock: _deny(engine, clock, scenario, view.run_id),
        )
        edit = None
        if scenario.edit_example is not None:
            edit = _branch(
                paused,
                root / "edit.sqlite",
                dataset,
                lambda engine, clock: _edit(engine, clock, scenario, view.run_id),
            )
        late = _branch(
            paused,
            root / "late.sqlite",
            dataset,
            lambda engine, clock: _late(engine, clock, view),
        )
        drafted = next(message for message in view.messages if message.role == "assistant")
        assert drafted.tool_call is not None
        expires = parse_iso(view.gate.expires_at)
        opened = parse_iso(view.created_at)
        seconds = int((expires - opened).total_seconds())
        return {
            "id": scenario.id,
            "title": scenario.title,
            "summary": scenario.summary,
            "lesson": scenario.lesson,
            "risk_label": scenario.risk_label,
            "tool": scenario.draft.tool,
            "task": scenario.task,
            "feature_expiry": scenario.feature_expiry,
            "has_edit": scenario.edit_example is not None,
            "steps_before": _steps_before(scenario, view, state_blob, state_bytes),
            "proposal": {
                "gate_id": view.gate.gate_id,
                "run_id": view.run_id,
                "tool": view.gate.tool_name,
                "risk_label": scenario.risk_label,
                "arguments": view.gate.arguments,
                "preview": tools.preview(view.gate.tool_name, view.gate.arguments),
                "expires_at": view.gate.expires_at,
                "ttl_label": _ttl_label(seconds),
                "commentary": drafted.content,
            },
            "audit_before": [item.model_dump(mode="json") for item in view.audit],
            "state_bytes": state_bytes,
            "continuations": {
                "approve": _pack(approve, pause_id, tools),
                "deny": _pack(deny, pause_id, tools, reason=scenario.deny_reason),
                "edit": None
                if edit is None
                else _pack(
                    edit,
                    pause_id,
                    tools,
                    reason=scenario.edit_example.reason if scenario.edit_example else None,
                    edited=scenario.edit_example.arguments if scenario.edit_example else None,
                ),
                "late": _pack(late, pause_id, tools),
            },
        }


def _engine(path: Path, dataset: Dataset, clock: ManualClock | None = None) -> Engine:
    return Engine(
        db_path=path,
        dataset=dataset,
        llm=MockProvider(),
        clock=clock or ManualClock(parse_iso(RECORD_START_ISO)),
        ids=StableIds(),
    )


def _branch(paused: Engine, dest: Path, dataset: Dataset, action) -> RunView:
    paused.store.backup_to(dest)
    clock = ManualClock(parse_iso(RECORD_START_ISO))
    engine = _engine(dest, dataset, clock)
    return action(engine, clock)


def _approve(engine: Engine, clock: ManualClock, scenario: Scenario, run_id: str) -> RunView:
    clock.advance(30)
    result = engine.decide(DecisionIn(decision="approve", actor=ACTOR), run_id=run_id)
    if scenario.duplicate_approve:
        clock.advance(5)
        result = engine.decide(DecisionIn(decision="approve", actor=ACTOR), run_id=run_id)
    return result.run


def _deny(engine: Engine, clock: ManualClock, scenario: Scenario, run_id: str) -> RunView:
    clock.advance(45)
    result = engine.decide(
        DecisionIn(decision="deny", actor=ACTOR, reason=scenario.deny_reason),
        run_id=run_id,
    )
    return result.run


def _edit(engine: Engine, clock: ManualClock, scenario: Scenario, run_id: str) -> RunView:
    assert scenario.edit_example is not None
    clock.advance(50)
    result = engine.decide(
        DecisionIn(
            decision="edit",
            actor=ACTOR,
            reason=scenario.edit_example.reason,
            edited_arguments=scenario.edit_example.arguments,
        ),
        run_id=run_id,
    )
    return result.run


def _late(engine: Engine, clock: ManualClock, paused: RunView) -> RunView:
    assert paused.gate is not None
    clock.current = parse_iso(paused.gate.expires_at) + timedelta(seconds=1)
    try:
        result = engine.decide(DecisionIn(decision="approve", actor=ACTOR), run_id=paused.run_id)
    except GateError as exc:
        if exc.run is None:
            raise
        return RunView.model_validate(exc.run)
    return result.run


def _state_blob(engine: Engine, run_id: str) -> tuple[str, int]:
    def read(con) -> str:
        row = Store.get_run(con, run_id)
        assert row is not None
        return row["state_json"]

    raw = engine.store.query(read)
    pretty = json.dumps(json.loads(raw), indent=2, sort_keys=True)
    return pretty, len(raw.encode())


def _pack(
    view: RunView,
    pause_id: int,
    tools: ToolRegistry,
    *,
    reason: str | None = None,
    edited: dict | None = None,
) -> dict:
    fresh = [item for item in view.audit if item.id > pause_id]
    preview = None
    if view.gate is not None:
        preview = tools.preview(view.gate.tool_name, view.gate.arguments)
    return {
        "actor": ACTOR,
        "reason": reason,
        "edited_arguments": edited,
        "preview": preview,
        "status": view.status,
        "final_answer": view.final_answer,
        "result": view.tool_result,
        "execution_count": view.tool_execution_count,
        "idempotent_replays": sum(1 for item in view.audit if item.event == "decision.replayed"),
        "steps": [_step(item, view) for item in fresh],
        "audit": [item.model_dump(mode="json") for item in fresh],
    }


def _steps_before(scenario: Scenario, view: RunView, state_blob: str, nbytes: int) -> list[dict]:
    drafted = next(message for message in view.messages if message.role == "assistant")
    assert drafted.tool_call is not None
    opened = next(item for item in view.audit if item.event == "gate.opened")
    return [
        {
            "kind": "user",
            "event": "run.started",
            "title": "Task",
            "body": scenario.task,
            "at": view.created_at,
        },
        {
            "kind": "model",
            "event": "model.drafted",
            "title": "Drafted a tool call",
            "body": drafted.content,
            "at": next(item.ts for item in view.audit if item.event == "model.drafted"),
            "code": json.dumps(
                {"tool": drafted.tool_call.name, "arguments": drafted.tool_call.arguments},
                indent=2,
            ),
        },
        {
            "kind": "persist",
            "event": "gate.opened",
            "title": "Serialized state and paused",
            "body": (
                f"Wrote {nbytes} bytes of agent state to SQLite and opened {opened.detail['gate_id']}. "
                "resume_cursor is execute_tool. The worker can exit here."
            ),
            "at": opened.ts,
            "code": state_blob,
            "collapse": True,
        },
    ]


def _step(audit, view: RunView) -> dict:
    event = audit.event
    detail = audit.detail
    base = {"kind": "system", "event": event, "title": event, "body": "", "at": audit.ts}
    if event == "decision.approved":
        base.update(
            kind="human",
            title=f"Approved by {audit.actor}",
            body="The gate was claimed in one transaction. An identical later click does not run the tool.",
        )
    elif event == "decision.edited":
        base.update(
            kind="human",
            title=f"Edited by {audit.actor}",
            body="The new arguments passed the same schema and policy checks as the draft.",
            code=json.dumps(detail.get("authorized_arguments"), indent=2, sort_keys=True),
        )
    elif event == "decision.denied":
        base.update(kind="human", title=f"Denied by {audit.actor}", body=detail.get("reason") or "")
    elif event == "decision.replayed":
        base.update(
            kind="warn",
            title="Duplicate click ignored",
            body="Same decision, already stored. tool.executed was not written again.",
        )
    elif event == "tool.executed":
        result = detail.get("result") or {}
        base.update(
            kind="tool",
            title=f"{result.get('tool')} executed once",
            body=summarize_result(result),
            code=json.dumps(result, indent=2, sort_keys=True),
        )
    elif event == "run.completed":
        base.update(kind="done", title="Run completed", body=view.final_answer or "")
    elif event == "run.denied":
        base.update(kind="stop", title="Stopped", body="The tool was not called.")
    elif event == "gate.expired":
        base.update(
            kind="warn",
            title="Gate expired",
            body=f"expires_at {detail.get('expires_at')} had passed. Nothing was executed.",
        )
    elif event == "decision.rejected_expired":
        base.update(
            kind="stop",
            title="Late decision rejected",
            body=f"{audit.actor} sent {detail.get('decision')} after expiry.",
        )
    return base


def _ttl_label(seconds: int) -> str:
    if seconds % 86400 == 0:
        days = seconds // 86400
        unit = "day" if days == 1 else "days"
        return f"{days} {unit}"
    if seconds % 3600 == 0:
        hours = seconds // 3600
        unit = "hour" if hours == 1 else "hours"
        return f"{hours} {unit}"
    return f"{seconds} seconds"


if __name__ == "__main__":
    main()
