"""HTTP API: JSON decisions, a Slack-style interactive payload, and a plain form.

Run with `uvicorn agent_gate.api:create_app --factory`.
"""

from __future__ import annotations

import json
import os
from contextlib import asynccontextmanager
from html import escape
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Form, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from pydantic import ValidationError

from agent_gate import __version__
from agent_gate.clock import ManualClock, SystemClock
from agent_gate.engine import Engine, StableIds, UuidIds
from agent_gate.errors import GateError
from agent_gate.models import CreateRun, DecisionIn, DecisionResult, RunSummary, RunView, ScenarioSummary

LIVE_PAGE = Path(__file__).with_name("live.html")


def create_app(
    *,
    db_path: str | Path | None = None,
    dataset_uri: str | None = None,
    llm_provider: str | None = None,
    clock: SystemClock | ManualClock | None = None,
    ids: UuidIds | StableIds | None = None,
) -> FastAPI:
    path = db_path or os.environ.get("HL_DB_PATH") or "var/gate.db"
    engine = Engine(
        db_path=path,
        dataset_uri=dataset_uri,
        llm_provider=llm_provider,
        clock=clock,
        ids=ids,
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.engine.recover()
        yield

    app = FastAPI(
        title="Approval Gate",
        version=__version__,
        summary="Durable human-in-the-loop pause for high-stakes agent tool calls.",
        lifespan=lifespan,
    )
    app.state.engine = engine

    @app.exception_handler(GateError)
    async def on_gate_error(request: Request, exc: GateError) -> JSONResponse:
        del request
        body: dict[str, Any] = {
            "code": exc.code,
            "message": exc.message,
            "idempotent_replay": exc.idempotent_replay,
        }
        if exc.errors is not None:
            body["errors"] = exc.errors
        if exc.run is not None:
            body["run"] = exc.run
        return JSONResponse(body, status_code=exc.status)

    @app.get("/health")
    def health() -> dict[str, Any]:
        current: Engine = app.state.engine
        return {
            "ok": True,
            "version": __version__,
            "provider": current.llm.name,
            "dataset": str(current.dataset.root),
        }

    @app.get("/v1/scenarios", response_model=list[ScenarioSummary])
    def scenarios() -> list[ScenarioSummary]:
        current: Engine = app.state.engine
        return [
            ScenarioSummary(
                id=item.id,
                title=item.title,
                summary=item.summary,
                lesson=item.lesson,
                task=item.task,
                risk_label=item.risk_label,
                tool=item.draft.tool,
            )
            for item in current.dataset.scenarios.values()
        ]

    @app.post("/v1/runs", status_code=201, response_model=RunView)
    def create_run(body: CreateRun) -> RunView:
        return app.state.engine.start(body.scenario_id)

    @app.get("/v1/runs", response_model=list[RunSummary])
    def list_runs() -> list[RunSummary]:
        return app.state.engine.list_summaries()

    @app.get("/v1/runs/{run_id}", response_model=RunView)
    def get_run(run_id: str) -> RunView:
        return app.state.engine.get(run_id)

    @app.post("/v1/runs/{run_id}/decisions", response_model=DecisionResult)
    def decide_run(run_id: str, body: DecisionIn) -> DecisionResult:
        return app.state.engine.decide(body, run_id=run_id)

    @app.post("/v1/gates/{gate_id}/decisions", response_model=DecisionResult)
    def decide_gate(gate_id: str, body: DecisionIn) -> DecisionResult:
        return app.state.engine.decide(body, gate_id=gate_id)

    @app.post("/v1/hooks/slack")
    async def slack(request: Request) -> dict[str, Any]:
        form = await request.form()
        raw = form.get("payload")
        if not isinstance(raw, str) or not raw:
            raise GateError(
                400,
                "bad_request",
                "Expected an application/x-www-form-urlencoded field named payload.",
            )
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise GateError(400, "bad_request", "Slack payload was not JSON.") from exc
        actions = payload.get("actions") or []
        if not actions:
            raise GateError(400, "bad_request", "Slack payload has no actions.")
        action = actions[0]
        try:
            value = json.loads(action.get("value") or "")
        except json.JSONDecodeError as exc:
            raise GateError(400, "bad_request", "Slack action value was not JSON.") from exc
        if not isinstance(value, dict):
            raise GateError(400, "bad_request", "Slack action value must be an object.")
        decision = value.get("decision") or _decision_from_action(str(action.get("action_id") or ""))
        user = payload.get("user") or {}
        actor = user.get("username") or user.get("id") or "slack.user"
        body = _decision_from_parts(
            decision=decision,
            actor=str(actor),
            reason=value.get("reason"),
            edited_arguments=value.get("edited_arguments"),
            idempotency_key=value.get("idempotency_key"),
        )
        gate_id = value.get("gate_id")
        if not gate_id:
            raise GateError(400, "bad_request", "Slack action value is missing gate_id.")
        result = app.state.engine.decide(body, gate_id=str(gate_id))
        text = _slack_text(result)
        return {"response_type": "ephemeral", "replace_original": False, "text": text}

    @app.get("/v1/gates/{gate_id}/form", response_class=HTMLResponse)
    def gate_form(gate_id: str) -> HTMLResponse:
        current: Engine = app.state.engine
        view = _run_for_gate(current, gate_id)
        return HTMLResponse(_form_html(view))

    @app.post("/v1/gates/{gate_id}/form", response_class=HTMLResponse)
    def submit_gate_form(
        gate_id: str,
        decision: str = Form(...),
        actor: str = Form("ops.reviewer"),
        reason: str = Form(""),
        edited_arguments: str = Form(""),
        idempotency_key: str = Form(""),
    ) -> HTMLResponse:
        edited: dict[str, Any] | None = None
        if decision == "edit":
            try:
                parsed = json.loads(edited_arguments or "")
            except json.JSONDecodeError as exc:
                return HTMLResponse(
                    _result_html(
                        title="Edit was not JSON",
                        message="The arguments box has to be a JSON object.",
                        status="awaiting_approval",
                    ),
                    status_code=422,
                )
            if not isinstance(parsed, dict):
                return HTMLResponse(
                    _result_html(
                        title="Edit was not an object",
                        message="The arguments box has to be a JSON object.",
                        status="awaiting_approval",
                    ),
                    status_code=422,
                )
            edited = parsed
        try:
            body = _decision_from_parts(
                decision=decision,
                actor=actor,
                reason=reason or None,
                edited_arguments=edited,
                idempotency_key=idempotency_key or None,
            )
            result = app.state.engine.decide(body, gate_id=gate_id)
        except GateError as exc:
            return HTMLResponse(
                _result_html(title=exc.code.replace("_", " "), message=exc.message, status=exc.code),
                status_code=exc.status,
            )
        run = result.run
        if result.idempotent_replay:
            title = "Already recorded"
            message = "This decision was already stored. The tool was not called again."
        elif run.status == "denied":
            title = "Denied"
            message = run.denial_reason or "Denied."
        elif run.status == "completed":
            title = "Executed once"
            message = run.final_answer or "Completed."
        else:
            title = run.status
            message = run.final_answer or run.status
        return HTMLResponse(_result_html(title=title, message=message, status=run.status))

    @app.post("/v1/maintenance/expire")
    def expire() -> dict[str, list[str]]:
        return {"expired": app.state.engine.expire_due()}

    @app.get("/", response_class=HTMLResponse)
    def index() -> FileResponse:
        return FileResponse(LIVE_PAGE)

    return app


def _decision_from_action(action_id: str) -> str:
    token = action_id.removeprefix("gate_")
    if token in {"approve", "deny", "edit"}:
        return token
    return action_id


def _decision_from_parts(
    *,
    decision: object,
    actor: str,
    reason: object,
    edited_arguments: object,
    idempotency_key: object,
) -> DecisionIn:
    try:
        return DecisionIn.model_validate(
            {
                "decision": decision,
                "actor": actor or "ops.reviewer",
                "reason": reason,
                "edited_arguments": edited_arguments,
                "idempotency_key": idempotency_key,
            }
        )
    except ValidationError as exc:
        message = exc.errors()[0]["msg"]
        raise GateError(422, "invalid_decision", message) from exc


def _run_for_gate(engine: Engine, gate_id: str) -> RunView:
    def read(con):
        row = con.execute("SELECT run_id FROM gates WHERE gate_id = ?", (gate_id,)).fetchone()
        return None if row is None else row[0]

    run_id = engine.store.query(read)
    if run_id is None:
        raise GateError(404, "not_found", f"No gate {gate_id}.")
    return engine.get(run_id)


def _slack_text(result: DecisionResult) -> str:
    run = result.run
    gate_id = run.gate.gate_id if run.gate else run.run_id
    if result.idempotent_replay:
        return (
            f"Already recorded. Gate {gate_id} is {run.status}. "
            "The tool was not called again."
        )
    if run.status == "completed" and run.final_answer:
        return run.final_answer
    if run.status == "denied":
        return f"Denied gate {gate_id}. {run.denial_reason or ''}".strip()
    return f"Gate {gate_id} is {run.status}."


def _form_html(run: RunView) -> str:
    gate = run.gate
    assert gate is not None
    rows = "".join(
        f"<div><dt>{escape(key)}</dt><dd>{escape(str(value))}</dd></div>"
        for key, value in gate.arguments.items()
    )
    args = escape(json.dumps(gate.arguments, indent=2, sort_keys=True))
    closed = gate.status != "open"
    buttons = ""
    if not closed:
        buttons = f"""
        <label>Decision
          <select name="decision">
            <option value="approve">Approve</option>
            <option value="deny">Deny</option>
            <option value="edit">Edit</option>
          </select>
        </label>
        <label>Actor <input name="actor" value="ops.reviewer"></label>
        <label>Reason <textarea name="reason" rows="3"></textarea></label>
        <label>Edited arguments (JSON, only for edit)
          <textarea name="edited_arguments" rows="8">{args}</textarea>
        </label>
        <button type="submit">Submit decision</button>
        """
    else:
        buttons = "<p>This gate is already closed. Submitting again is idempotent only for the same decision.</p>"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Gate {escape(gate.gate_id)}</title>
  <style>
    body {{ font: 16px/1.45 "Segoe UI", sans-serif; margin: 2rem auto; max-width: 40rem;
            background: #f3efe6; color: #1b1714; }}
    dl div {{ display: grid; grid-template-columns: 8rem 1fr; gap: 0.5rem; }}
    dt {{ color: #5e564c; }}
    textarea, input, select {{ width: 100%; font: inherit; }}
    button {{ margin-top: 1rem; padding: 0.6rem 1rem; }}
  </style>
</head>
<body>
  <p>Houghton Labs · Approval Gate</p>
  <h1>{escape(gate.tool_name)}</h1>
  <p>Status {escape(gate.status)} · expires {escape(gate.expires_at)}</p>
  <dl>{rows}</dl>
  <form method="post">
    {buttons}
  </form>
</body>
</html>
"""


def _result_html(*, title: str, message: str, status: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{escape(title)}</title>
  <style>
    body {{ font: 16px/1.45 "Segoe UI", sans-serif; margin: 2rem auto; max-width: 40rem;
            background: #f3efe6; color: #1b1714; }}
  </style>
</head>
<body>
  <p>Houghton Labs · Approval Gate</p>
  <h1>{escape(title)}</h1>
  <p>{escape(message)}</p>
  <p>Status: {escape(status)}</p>
</body>
</html>
"""
