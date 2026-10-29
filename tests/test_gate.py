import json
import sqlite3

import pytest

from agent_gate.engine import Engine
from agent_gate.errors import GateError
from agent_gate.models import DecisionIn


def _approve(engine: Engine, run_id: str):
    return engine.decide(DecisionIn(decision="approve", actor="ops.reviewer"), run_id=run_id)


def _deny(engine: Engine, run_id: str, reason: str = "Do not do this yet."):
    return engine.decide(
        DecisionIn(decision="deny", actor="ops.reviewer", reason=reason),
        run_id=run_id,
    )


def test_approve_executes_once_and_a_second_click_does_not(engine: Engine):
    view = engine.start("refund-stalled")
    assert view.status == "awaiting_approval"
    assert view.resume_cursor == "execute_tool"
    assert [message.role for message in view.messages] == ["system", "user", "assistant"]

    first = _approve(engine, view.run_id)
    assert first.code == "approved"
    assert first.idempotent_replay is False
    assert first.run.status == "completed"
    assert first.run.tool_execution_count == 1
    assert first.run.final_answer.startswith("Issued refund RF-")
    assert first.run.tool_result["amount_usd"] == "86.40"

    second = _approve(engine, view.run_id)
    assert second.idempotent_replay is True
    assert second.run.tool_execution_count == 1
    assert second.run.final_answer == first.run.final_answer
    events = [item.event for item in second.run.audit]
    assert events.count("tool.executed") == 1
    assert "decision.replayed" in events


def test_deny_records_the_reason_and_does_not_execute(engine: Engine):
    view = engine.start("email-vendor")
    reason = "Finance already has a thread open with the vendor. Do not send another."
    result = _deny(engine, view.run_id, reason)
    assert result.run.status == "denied"
    assert result.run.denial_reason == reason
    assert result.run.tool_execution_count == 0
    assert result.run.tool_result is None
    again = _deny(engine, view.run_id, reason)
    assert again.idempotent_replay is True
    assert again.run.tool_execution_count == 0


def test_conflicting_decision_is_rejected(engine: Engine):
    view = engine.start("dns-cutover")
    _approve(engine, view.run_id)
    with pytest.raises(GateError) as caught:
        _deny(engine, view.run_id, "Change window is frozen until the status name is moved.")
    assert caught.value.status == 409
    assert caught.value.code == "conflict"
    saved = engine.get(view.run_id)
    assert saved.status == "completed"
    assert saved.tool_execution_count == 1
    assert any(item.event == "decision.conflict" for item in saved.audit)


def test_edit_revalidates_and_executes_the_authorized_arguments(engine: Engine):
    view = engine.start("refund-goodwill")
    assert view.messages[2].tool_call is not None
    assert view.messages[2].tool_call.arguments["amount_usd"] == "86.40"
    edited = {
        "order_id": "NW-18442",
        "amount_usd": "43.20",
        "reason": "Partial goodwill while the carrier trace stays open.",
    }
    result = engine.decide(
        DecisionIn(
            decision="edit",
            actor="ops.reviewer",
            reason="Reviewer reduced the refund to half while the trace stays open.",
            edited_arguments=edited,
        ),
        run_id=view.run_id,
    )
    assert result.code == "edited"
    assert result.run.tool_result["amount_usd"] == "43.20"
    assert result.run.gate is not None
    assert result.run.gate.proposed_arguments["amount_usd"] == "86.40"
    assert result.run.gate.arguments["amount_usd"] == "43.20"
    assert result.run.messages[2].tool_call is not None
    assert result.run.messages[2].tool_call.arguments["amount_usd"] == "86.40"
    replay = engine.decide(
        DecisionIn(
            decision="edit",
            actor="ops.reviewer",
            reason="Reviewer reduced the refund to half while the trace stays open.",
            edited_arguments=edited,
        ),
        run_id=view.run_id,
    )
    assert replay.idempotent_replay is True
    assert replay.run.tool_execution_count == 1


def test_invalid_edit_leaves_the_gate_open(engine: Engine):
    view = engine.start("refund-stalled")
    edited = dict(view.gate.arguments)
    edited["amount_usd"] = "200.00"
    with pytest.raises(GateError) as caught:
        engine.decide(
            DecisionIn(decision="edit", actor="ops.reviewer", edited_arguments=edited),
            run_id=view.run_id,
        )
    assert caught.value.status == 422
    assert caught.value.code == "edit_rejected"
    assert engine.get(view.run_id).status == "awaiting_approval"
    done = _approve(engine, view.run_id)
    assert done.run.tool_result["amount_usd"] == "86.40"


def test_short_reason_and_public_dns_and_unknown_mailbox_are_rejected(engine: Engine):
    refund = engine.start("refund-stalled")
    short = dict(refund.gate.arguments)
    short["reason"] = "no"
    with pytest.raises(GateError) as caught:
        engine.decide(
            DecisionIn(decision="edit", actor="ops.reviewer", edited_arguments=short),
            run_id=refund.run_id,
        )
    assert caught.value.status == 422

    dns = engine.start("dns-cutover")
    public = dict(dns.gate.arguments)
    public["value"] = "8.8.8.8"
    with pytest.raises(GateError) as caught:
        engine.decide(
            DecisionIn(decision="edit", actor="ops.reviewer", edited_arguments=public),
            run_id=dns.run_id,
        )
    assert "203.0.113.0/24" in caught.value.errors[0]["msg"]
    assert engine.get(dns.run_id).status == "awaiting_approval"

    mail = engine.start("email-vendor")
    outsider = dict(mail.gate.arguments)
    outsider["to"] = "outsider@not-in-directory.example"
    with pytest.raises(GateError):
        engine.decide(
            DecisionIn(decision="edit", actor="ops.reviewer", edited_arguments=outsider),
            run_id=mail.run_id,
        )
    assert engine.get(mail.run_id).status == "awaiting_approval"


def test_expiry_on_decision_and_sweep(engine: Engine, clock):
    view = engine.start("refund-expired")
    clock.advance(3601)
    with pytest.raises(GateError) as caught:
        _approve(engine, view.run_id)
    assert caught.value.status == 410
    assert caught.value.idempotent_replay is False
    saved = engine.get(view.run_id)
    assert saved.status == "expired"
    assert saved.tool_execution_count == 0

    other = engine.start("dns-cutover")
    clock.advance(14401)
    expired = engine.expire_due()
    assert other.gate.gate_id in expired
    with pytest.raises(GateError) as caught:
        _approve(engine, other.run_id)
    assert caught.value.status == 410
    assert caught.value.idempotent_replay is True
    assert engine.get(other.run_id).tool_execution_count == 0


def test_invalid_draft_opens_no_gate(engine: Engine):
    scenario = engine.dataset.scenarios["refund-stalled"]
    arguments = dict(scenario.draft.arguments)
    arguments["amount_usd"] = "9999.00"
    engine.dataset.scenarios["refund-stalled"] = scenario.model_copy(
        update={"draft": scenario.draft.model_copy(update={"arguments": arguments})}
    )
    with pytest.raises(GateError) as caught:
        engine.start("refund-stalled")
    assert caught.value.status == 422
    assert caught.value.code == "invalid_draft"
    view = engine.get(caught.value.run["run_id"])
    assert view.status == "failed"
    assert view.gate is None


def test_disputed_order_fails_before_a_gate(engine: Engine):
    scenario = engine.dataset.scenarios["refund-stalled"]
    arguments = dict(scenario.draft.arguments)
    arguments["order_id"] = "NW-20001"
    arguments["amount_usd"] = "50.00"
    engine.dataset.scenarios["refund-stalled"] = scenario.model_copy(
        update={"draft": scenario.draft.model_copy(update={"arguments": arguments})}
    )
    with pytest.raises(GateError) as caught:
        engine.start("refund-stalled")
    assert "dispute" in caught.value.errors[0]["msg"]


def test_low_stakes_tool_skips_the_human_gate(engine: Engine):
    policy = engine.dataset.policy.tools["issue_refund"]
    engine.dataset.policy.tools["issue_refund"] = policy.model_copy(
        update={"requires_approval": False}
    )
    view = engine.start("refund-stalled")
    assert view.status == "completed"
    assert view.tool_execution_count == 1
    assert all(item.event != "gate.opened" for item in view.audit)
    assert any(item.event == "gate.bypassed" for item in view.audit)


def test_unknown_scenario_and_state_roundtrip(tmp_path, dataset_uri, clock):
    engine = Engine(
        db_path=tmp_path / "gate.db",
        dataset_uri=dataset_uri,
        llm_provider="mock",
        clock=clock,
    )
    with pytest.raises(GateError) as caught:
        engine.start("no-such-scenario")
    assert caught.value.status == 404

    view = engine.start("dns-cutover")
    reloaded = Engine(
        db_path=tmp_path / "gate.db",
        dataset_uri=dataset_uri,
        llm_provider="mock",
        clock=clock,
    )
    assert reloaded.get(view.run_id).model_dump() == view.model_dump()

    def raw(con):
        return con.execute("SELECT state_json FROM runs").fetchone()[0]

    blob = json.loads(engine.store.query(raw))
    assert blob["resume_cursor"] == "execute_tool"
    assert blob["messages"][0]["role"] == "system"


def test_effect_row_is_unique_per_gate(engine: Engine):
    view = engine.start("refund-stalled")
    _approve(engine, view.run_id)

    def count(con):
        return con.execute("SELECT COUNT(*) FROM effects").fetchone()[0]

    assert engine.store.query(count) == 1
    with pytest.raises(sqlite3.IntegrityError):
        with engine.store.transaction() as con:
            engine.store.insert_effect(
                con,
                effect_id="RF-OTHER01",
                gate_id=view.gate.gate_id,
                tool_name="issue_refund",
                result={"ok": True},
                now="2026-10-28T15:00:00Z",
            )
    assert engine.store.query(count) == 1
