"""Draft, pause, and resume.

The pause is a row, not a sleeping thread. `decide` claims the gate in one
transaction. The mock tool runs only after that commit, and the effect row is
unique on gate id, so a duplicate click or a recovered crash cannot execute twice.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from agent_gate.clock import ManualClock, SystemClock, iso, parse_iso
from agent_gate.dataset import Dataset, load_dataset
from agent_gate.errors import ArgError, GateError
from agent_gate.llm import SYSTEM_PROMPT, LLM, build_llm
from agent_gate.models import (
    AgentState,
    AuditView,
    DecisionIn,
    DecisionResult,
    GateView,
    Message,
    RunSummary,
    RunView,
    ToolCall,
)
from agent_gate.store import Store, dumps
from agent_gate.tools import ToolRegistry, summarize_result


class UuidIds:
    def run_id(self, scenario_id: str) -> str:
        del scenario_id
        return "run_" + uuid.uuid4().hex[:12]

    def gate_id(self, scenario_id: str) -> str:
        del scenario_id
        return "gate_" + uuid.uuid4().hex[:12]

    def tool_call_id(self, scenario_id: str) -> str:
        del scenario_id
        return "call_" + uuid.uuid4().hex[:8]


class StableIds:
    """Ids derived from the scenario, so the recorded site JSON stays diff-stable."""

    def run_id(self, scenario_id: str) -> str:
        return f"run_{scenario_id}"

    def gate_id(self, scenario_id: str) -> str:
        return f"gate_{scenario_id}"

    def tool_call_id(self, scenario_id: str) -> str:
        return f"call_{scenario_id}"


@dataclass
class _Claim:
    error: GateError | None = None
    execute: bool = False
    run_id: str | None = None
    origin: str | None = None
    result: DecisionResult | None = None


class Engine:
    def __init__(
        self,
        *,
        db_path: str,
        dataset_uri: str | None = None,
        llm_provider: str | None = None,
        clock: SystemClock | ManualClock | None = None,
        ids: UuidIds | StableIds | None = None,
        dataset: Dataset | None = None,
        llm: LLM | None = None,
    ) -> None:
        self.store = Store(db_path)
        self.dataset = dataset or load_dataset(dataset_uri)
        self.llm = llm or build_llm(llm_provider, self.dataset)
        self.tools = ToolRegistry(self.dataset)
        self.clock = clock or SystemClock()
        self.ids = ids or UuidIds()

    def start(self, scenario_id: str) -> RunView:
        scenario = self.dataset.scenario(scenario_id)
        now_s = iso(self.clock.now())
        state = AgentState(
            run_id=self.ids.run_id(scenario_id),
            scenario_id=scenario_id,
            status="running",
            messages=[
                Message(role="system", content=SYSTEM_PROMPT),
                Message(role="user", content=scenario.task),
            ],
            resume_cursor="draft",
            created_at=now_s,
            updated_at=now_s,
        )
        with self.store.transaction() as con:
            self.store.insert_run(con, state)
            self._audit(
                con,
                state,
                event="run.started",
                actor="agent",
                detail={"scenario_id": scenario_id},
            )
        try:
            turn = self.llm.complete(state.messages, self.tools.specs(), scenario)
        except GateError as exc:
            self._fail(state, "The model provider failed while drafting.", [])
            raise exc
        if turn.tool_call is not None and not turn.tool_call.id:
            turn.tool_call.id = self.ids.tool_call_id(scenario_id)
        now_s = iso(self.clock.now())
        state.messages.append(
            Message(role="assistant", content=turn.content, tool_call=turn.tool_call)
        )
        state.updated_at = now_s
        if turn.tool_call is None:
            state.status = "completed"
            state.final_answer = turn.content
            state.resume_cursor = "stopped"
            with self.store.transaction() as con:
                self.store.save_state(con, state)
                self._audit(
                    con,
                    state,
                    event="run.completed",
                    actor="agent",
                    detail={"final_answer": turn.content},
                )
            return self.get(state.run_id)

        try:
            authorized = self.tools.validate(turn.tool_call.name, turn.tool_call.arguments)
        except ArgError as exc:
            state.status = "failed"
            state.error = exc.errors
            state.resume_cursor = "stopped"
            with self.store.transaction() as con:
                self.store.save_state(con, state)
                self._audit(
                    con,
                    state,
                    event="model.drafted",
                    actor="agent",
                    detail={"tool": turn.tool_call.name, "arguments": turn.tool_call.arguments},
                )
                self._audit(
                    con,
                    state,
                    event="run.failed",
                    actor="agent",
                    detail={"errors": exc.errors},
                )
            view = self.get(state.run_id)
            raise GateError(
                422,
                "invalid_draft",
                "The draft failed validation. No gate was opened.",
                errors=exc.errors,
                run=view.model_dump(mode="json"),
            ) from exc

        turn.tool_call.arguments = authorized
        state.messages[-1] = Message(
            role="assistant",
            content=turn.content,
            tool_call=turn.tool_call,
        )
        policy = self.tools.policy_for(turn.tool_call.name)
        ttl = scenario.ttl_seconds if scenario.ttl_seconds is not None else policy.ttl_seconds
        expires_at = iso(parse_iso(now_s) + timedelta(seconds=ttl))
        human = policy.requires_approval
        self._open_gate(state, turn.tool_call, expires_at, now_s, human=human)
        if human:
            return self.get(state.run_id)
        return self._execute(state.run_id, origin="approved").run

    def decide(
        self,
        body: DecisionIn,
        *,
        run_id: str | None = None,
        gate_id: str | None = None,
    ) -> DecisionResult:
        if run_id is None and gate_id is None:
            raise GateError(400, "bad_request", "A run id or a gate id is required.")
        claim = self._claim(body, run_id=run_id, gate_id=gate_id)
        if claim.error is not None:
            raise claim.error
        if claim.execute:
            assert claim.run_id is not None
            return self._execute(claim.run_id, origin=claim.origin or "approved")
        assert claim.result is not None
        return claim.result

    def recover(self) -> int:
        """Finish gates left in `executing` when a process died after the claim.

        Awaiting gates are left alone. That is the durable pause.
        """
        finished = 0
        for run_id in self.store.list_run_ids("executing"):
            try:
                self._execute(run_id)
            except GateError:
                continue
            finished += 1
        return finished

    def expire_due(self) -> list[str]:
        now_s = iso(self.clock.now())
        expired: list[str] = []
        with self.store.transaction() as con:
            rows = con.execute(
                """
                SELECT * FROM gates
                WHERE status = 'open' AND expires_at <= ?
                ORDER BY gate_id
                """,
                (now_s,),
            ).fetchall()
            for gate in rows:
                run = Store.get_run(con, gate["run_id"])
                assert run is not None
                state = Store.load_state(run)
                self._mark_expired(con, state, gate, now_s, attempt=None)
                expired.append(gate["gate_id"])
        return expired

    def get(self, run_id: str) -> RunView:
        def read(con):
            row = Store.get_run(con, run_id)
            if row is None:
                return None
            gate = Store.get_gate_for_run(con, run_id)
            audit = Store.audit_rows(con, run_id)
            return _compose(Store.load_state(row), gate, audit)

        view = self.store.query(read)
        if view is None:
            raise GateError(404, "not_found", f"No run {run_id}.")
        return view

    def list_summaries(self) -> list[RunSummary]:
        def read(con):
            rows = con.execute(
                """
                SELECT r.run_id, r.scenario_id, r.status, r.created_at, r.updated_at,
                       g.gate_id, g.tool_name, g.expires_at
                FROM runs r
                LEFT JOIN gates g ON g.run_id = r.run_id
                ORDER BY r.created_at, r.run_id
                """
            )
            return [
                RunSummary(
                    run_id=row["run_id"],
                    scenario_id=row["scenario_id"],
                    status=row["status"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    tool_name=row["tool_name"],
                    gate_id=row["gate_id"],
                    expires_at=row["expires_at"],
                )
                for row in rows
            ]

        return self.store.query(read)

    def _open_gate(
        self,
        state: AgentState,
        call: ToolCall,
        expires_at: str,
        now_s: str,
        *,
        human: bool,
    ) -> None:
        gate_id = self.ids.gate_id(state.scenario_id)
        state.gate_id = gate_id
        state.pending_call = call.model_copy(deep=True)
        state.updated_at = now_s
        if human:
            state.status = "awaiting_approval"
            state.resume_cursor = "execute_tool"
        else:
            state.status = "executing"
            state.resume_cursor = "execute_tool"
        with self.store.transaction() as con:
            self.store.insert_gate(
                con,
                gate_id=gate_id,
                run_id=state.run_id,
                tool_name=call.name,
                arguments=call.arguments,
                expires_at=expires_at,
                now=now_s,
            )
            self.store.save_state(con, state)
            self._audit(
                con,
                state,
                event="model.drafted",
                actor="agent",
                detail={
                    "tool": call.name,
                    "arguments": call.arguments,
                    "commentary": state.messages[-1].content,
                },
            )
            if human:
                self._audit(
                    con,
                    state,
                    event="gate.opened",
                    actor="agent",
                    detail={
                        "gate_id": gate_id,
                        "tool": call.name,
                        "arguments": call.arguments,
                        "expires_at": expires_at,
                        "resume_cursor": "execute_tool",
                    },
                )
            else:
                decision = {
                    "decision": "approve",
                    "actor": "policy",
                    "reason": "This tool does not require a human.",
                    "edited_arguments": None,
                    "authorized_arguments": call.arguments,
                    "proposed_arguments": call.arguments,
                    "idempotency_key": None,
                }
                con.execute(
                    """
                    UPDATE gates
                    SET status = 'claimed', decision_json = ?, updated_at = ?
                    WHERE gate_id = ?
                    """,
                    (dumps(decision), now_s, gate_id),
                )
                self._audit(
                    con,
                    state,
                    event="gate.bypassed",
                    actor="policy",
                    detail={"gate_id": gate_id, "tool": call.name},
                )

    def _claim(
        self,
        body: DecisionIn,
        *,
        run_id: str | None,
        gate_id: str | None,
    ) -> _Claim:
        now_s = iso(self.clock.now())
        outcome = _Claim()
        with self.store.transaction() as con:
            gate, state, missing = self._load_for_decision(con, run_id, gate_id)
            if missing is not None:
                outcome.error = missing
                return outcome
            assert gate is not None and state is not None
            outcome.run_id = state.run_id
            if gate["status"] == "expired" or state.status == "expired":
                self._audit(
                    con,
                    state,
                    event="decision.rejected_expired",
                    actor=body.actor,
                    detail={"decision": body.decision},
                    now=now_s,
                )
                state.updated_at = now_s
                self.store.save_state(con, state)
                view = self._view(con, state.run_id)
                outcome.error = GateError(
                    410,
                    "expired",
                    "This gate expired before the decision. The tool was not called.",
                    run=view.model_dump(mode="json"),
                    idempotent_replay=True,
                )
                return outcome
            if gate["status"] == "open":
                if gate["expires_at"] <= now_s:
                    self._mark_expired(con, state, gate, now_s, attempt=body)
                    view = self._view(con, state.run_id)
                    outcome.error = GateError(
                        410,
                        "expired",
                        "This gate expired before the decision. The tool was not called.",
                        run=view.model_dump(mode="json"),
                    )
                    return outcome
                return self._claim_open(con, outcome, state, gate, body, now_s)
            return self._claim_closed(con, outcome, state, gate, body, now_s)
        return outcome

    def _claim_open(self, con, outcome: _Claim, state, gate, body: DecisionIn, now_s: str) -> _Claim:
        proposed = json.loads(gate["proposed_json"])
        authorized = json.loads(gate["arguments_json"])
        if body.decision == "deny":
            decision = _decision_doc(body, authorized=None, proposed=proposed)
            state.status = "denied"
            state.denial_reason = body.reason
            state.resume_cursor = "stopped"
            state.updated_at = now_s
            self._write_gate(
                con,
                gate,
                status="denied",
                arguments=authorized,
                decision=decision,
                execution=None,
                now_s=now_s,
            )
            self.store.save_state(con, state)
            self._audit(
                con,
                state,
                event="decision.denied",
                actor=body.actor,
                detail={"reason": body.reason},
                now=now_s,
            )
            self._audit(
                con,
                state,
                event="run.denied",
                actor="agent",
                detail={"reason": body.reason},
                now=now_s,
            )
            outcome.result = DecisionResult(
                code="denied",
                run=self._view(con, state.run_id),
            )
            return outcome
        if body.decision == "edit":
            assert body.edited_arguments is not None
            try:
                authorized = self.tools.validate(gate["tool_name"], body.edited_arguments)
            except ArgError as exc:
                self._audit(
                    con,
                    state,
                    event="edit.rejected",
                    actor=body.actor,
                    detail={"errors": exc.errors, "edited_arguments": body.edited_arguments},
                    now=now_s,
                )
                state.updated_at = now_s
                self.store.save_state(con, state)
                view = self._view(con, state.run_id)
                outcome.error = GateError(
                    422,
                    "edit_rejected",
                    "Edited arguments failed validation. The gate is still open.",
                    errors=exc.errors,
                    run=view.model_dump(mode="json"),
                )
                return outcome
        decision = _decision_doc(body, authorized=authorized, proposed=proposed)
        if state.pending_call is None:
            state.pending_call = ToolCall(name=gate["tool_name"], arguments=authorized)
        else:
            state.pending_call.arguments = authorized
        state.status = "executing"
        state.resume_cursor = "execute_tool"
        state.updated_at = now_s
        self._write_gate(
            con,
            gate,
            status="claimed",
            arguments=authorized,
            decision=decision,
            execution=None,
            now_s=now_s,
        )
        self.store.save_state(con, state)
        event = "decision.edited" if body.decision == "edit" else "decision.approved"
        self._audit(
            con,
            state,
            event=event,
            actor=body.actor,
            detail={
                "authorized_arguments": authorized,
                "proposed_arguments": proposed,
                "reason": body.reason,
            },
            now=now_s,
        )
        outcome.execute = True
        outcome.origin = "edited" if body.decision == "edit" else "approved"
        outcome.run_id = state.run_id
        return outcome

    def _claim_closed(self, con, outcome: _Claim, state, gate, body: DecisionIn, now_s: str) -> _Claim:
        if not gate["decision_json"]:
            outcome.error = GateError(
                409,
                "conflict",
                f"Run is {state.status} and has no stored decision.",
            )
            return outcome
        stored = json.loads(gate["decision_json"])
        if _same_decision(stored, body):
            if gate["execution_json"] is None and state.status == "executing":
                outcome.execute = True
                outcome.origin = "edited" if stored.get("decision") == "edit" else "approved"
                outcome.run_id = state.run_id
                return outcome
            self._audit(
                con,
                state,
                event="decision.replayed",
                actor=body.actor,
                detail={"decision": body.decision, "idempotency_key": body.idempotency_key},
                now=now_s,
            )
            state.updated_at = now_s
            self.store.save_state(con, state)
            outcome.result = DecisionResult(
                code="replayed",
                idempotent_replay=True,
                run=self._view(con, state.run_id),
            )
            return outcome
        key = stored.get("idempotency_key")
        if key and key == body.idempotency_key:
            message = (
                f"Idempotency key {key} was already used for {stored.get('decision')}."
            )
        else:
            message = f"This gate was already {stored.get('decision')}."
        self._audit(
            con,
            state,
            event="decision.conflict",
            actor=body.actor,
            detail={"attempt": body.decision, "stored": stored.get("decision")},
            now=now_s,
        )
        view = self._view(con, state.run_id)
        outcome.error = GateError(409, "conflict", message, run=view.model_dump(mode="json"))
        return outcome

    def _execute(self, run_id: str, *, origin: str | None = None) -> DecisionResult:
        try:
            return self._execute_locked(run_id, origin=origin)
        except ArgError as exc:
            self._fail_id(run_id, "Authorized arguments failed at execution.", exc.errors)
            raise GateError(
                422,
                "invalid_arguments",
                "Authorized arguments failed at execution.",
                errors=exc.errors,
            ) from exc

    def _execute_locked(self, run_id: str, *, origin: str | None) -> DecisionResult:
        now_s = iso(self.clock.now())
        with self.store.transaction() as con:
            run = Store.get_run(con, run_id)
            if run is None:
                raise GateError(404, "not_found", f"No run {run_id}.")
            state = Store.load_state(run)
            gate = Store.get_gate_for_run(con, run_id)
            if gate is None:
                raise GateError(409, "conflict", "This run has no gate to execute.")
            if state.status == "completed" or gate["execution_json"]:
                return DecisionResult(
                    code="replayed",
                    idempotent_replay=True,
                    run=self._view(con, run_id),
                )
            if state.status != "executing":
                raise GateError(409, "conflict", f"Run is {state.status}, not executing.")
            arguments = json.loads(gate["arguments_json"])
            result = self.tools.perform(gate["tool_name"], arguments, gate_id=gate["gate_id"])
            effect_id = result.get("refund_id") or result.get("message_id") or result.get("change_id")
            self.store.insert_effect(
                con,
                effect_id=str(effect_id),
                gate_id=gate["gate_id"],
                tool_name=gate["tool_name"],
                result=result,
                now=now_s,
            )
            state.messages.append(
                Message(role="tool", content=dumps(result), tool_name=gate["tool_name"])
            )
            scenario = self.dataset.scenario(state.scenario_id)
            final = self._final_sentence(state, scenario, result)
            state.messages.append(Message(role="assistant", content=final))
            state.tool_result = result
            state.final_answer = final
            state.status = "completed"
            state.resume_cursor = "stopped"
            state.updated_at = now_s
            stored = json.loads(gate["decision_json"]) if gate["decision_json"] else {}
            origin = origin or ("edited" if stored.get("decision") == "edit" else "approved")
            self._write_gate(
                con,
                gate,
                status="executed",
                arguments=arguments,
                decision=stored,
                execution=result,
                now_s=now_s,
            )
            self.store.save_state(con, state)
            self._audit(
                con,
                state,
                event="tool.executed",
                actor="agent",
                detail={"result": result, "effect_id": effect_id},
                now=now_s,
            )
            self._audit(
                con,
                state,
                event="run.completed",
                actor="agent",
                detail={"final_answer": final},
                now=now_s,
            )
            return DecisionResult(code=origin, run=self._view(con, run_id))

    def _final_sentence(self, state: AgentState, scenario, result: dict[str, Any]) -> str:
        try:
            turn = self.llm.complete(state.messages, self.tools.specs(), scenario)
        except GateError:
            raise
        if turn.tool_call is not None or not turn.content.strip():
            return summarize_result(result)
        return turn.content.strip()

    def _mark_expired(self, con, state: AgentState, gate, now_s: str, *, attempt: DecisionIn | None) -> None:
        state.status = "expired"
        state.resume_cursor = "stopped"
        state.updated_at = now_s
        self._write_gate(
            con,
            gate,
            status="expired",
            arguments=json.loads(gate["arguments_json"]),
            decision={"decision": "expired"},
            execution=None,
            now_s=now_s,
        )
        self.store.save_state(con, state)
        self._audit(
            con,
            state,
            event="gate.expired",
            actor="clock",
            detail={"expires_at": gate["expires_at"]},
            now=now_s,
        )
        if attempt is not None:
            self._audit(
                con,
                state,
                event="decision.rejected_expired",
                actor=attempt.actor,
                detail={"decision": attempt.decision},
                now=now_s,
            )

    def _load_for_decision(self, con, run_id: str | None, gate_id: str | None):
        if gate_id is not None:
            gate = Store.get_gate(con, gate_id)
            if gate is None:
                return None, None, GateError(404, "not_found", f"No gate {gate_id}.")
            run = Store.get_run(con, gate["run_id"])
        else:
            assert run_id is not None
            run = Store.get_run(con, run_id)
            if run is None:
                return None, None, GateError(404, "not_found", f"No run {run_id}.")
            gate = Store.get_gate_for_run(con, run_id)
            if gate is None:
                return (
                    None,
                    None,
                    GateError(409, "conflict", "This run has no approval gate."),
                )
        assert run is not None
        return gate, Store.load_state(run), None

    def _write_gate(
        self,
        con,
        gate,
        *,
        status: str,
        arguments: dict | None,
        decision: dict | None,
        execution: dict | None,
        now_s: str,
    ) -> None:
        con.execute(
            """
            UPDATE gates
            SET status = ?, arguments_json = ?, decision_json = ?, execution_json = ?, updated_at = ?
            WHERE gate_id = ?
            """,
            (
                status,
                dumps(arguments) if arguments is not None else gate["arguments_json"],
                dumps(decision) if decision is not None else gate["decision_json"],
                dumps(execution) if execution is not None else gate["execution_json"],
                now_s,
                gate["gate_id"],
            ),
        )

    def _view(self, con, run_id: str) -> RunView:
        row = Store.get_run(con, run_id)
        assert row is not None
        gate = Store.get_gate_for_run(con, run_id)
        audit = Store.audit_rows(con, run_id)
        return _compose(Store.load_state(row), gate, audit)

    def _audit(
        self,
        con,
        state: AgentState,
        *,
        event: str,
        actor: str,
        detail: dict[str, Any],
        now: str | None = None,
    ) -> None:
        self.store.add_audit(
            con,
            run_id=state.run_id,
            gate_id=state.gate_id,
            ts=now or state.updated_at,
            actor=actor,
            event=event,
            detail=detail,
        )

    def _fail(self, state: AgentState, message: str, errors: list[dict[str, str]]) -> None:
        now_s = iso(self.clock.now())
        state.status = "failed"
        state.resume_cursor = "stopped"
        state.error = errors or [{"loc": "provider", "msg": message}]
        state.updated_at = now_s
        with self.store.transaction() as con:
            self.store.save_state(con, state)
            self._audit(
                con,
                state,
                event="run.failed",
                actor="agent",
                detail={"message": message, "errors": state.error},
            )

    def _fail_id(self, run_id: str, message: str, errors: list[dict[str, str]]) -> None:
        with self.store.transaction() as con:
            row = Store.get_run(con, run_id)
            if row is None:
                return
            state = Store.load_state(row)
        self._fail(state, message, errors)


def _decision_doc(body: DecisionIn, *, authorized: dict | None, proposed: dict) -> dict:
    return {
        "decision": body.decision,
        "actor": body.actor,
        "reason": body.reason,
        "edited_arguments": body.edited_arguments if body.decision == "edit" else None,
        "authorized_arguments": authorized,
        "proposed_arguments": proposed,
        "idempotency_key": body.idempotency_key,
    }


def _same_decision(stored: dict, body: DecisionIn) -> bool:
    if stored.get("decision") != body.decision:
        return False
    if body.decision == "edit":
        return dumps(stored.get("edited_arguments")) == dumps(body.edited_arguments)
    if body.decision == "deny":
        return (stored.get("reason") or "") == (body.reason or "")
    return True


def _compose(state: AgentState, gate, audit_rows) -> RunView:
    audits = [
        AuditView(
            id=row["id"],
            ts=row["ts"],
            actor=row["actor"],
            event=row["event"],
            detail=json.loads(row["detail_json"]),
            gate_id=row["gate_id"],
        )
        for row in audit_rows
    ]
    gate_view = None
    if gate is not None:
        gate_view = GateView(
            gate_id=gate["gate_id"],
            tool_name=gate["tool_name"],
            arguments=json.loads(gate["arguments_json"]),
            proposed_arguments=json.loads(gate["proposed_json"]),
            status=gate["status"],
            expires_at=gate["expires_at"],
            decision=json.loads(gate["decision_json"]) if gate["decision_json"] else None,
            execution=json.loads(gate["execution_json"]) if gate["execution_json"] else None,
        )
    return RunView(
        run_id=state.run_id,
        scenario_id=state.scenario_id,
        status=state.status,
        created_at=state.created_at,
        updated_at=state.updated_at,
        resume_cursor=state.resume_cursor,
        messages=state.messages,
        pending_call=state.pending_call,
        gate=gate_view,
        tool_result=state.tool_result,
        final_answer=state.final_answer,
        denial_reason=state.denial_reason,
        error=state.error,
        tool_execution_count=sum(1 for item in audits if item.event == "tool.executed"),
        audit=audits,
    )
