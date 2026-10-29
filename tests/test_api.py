import json


def test_health_scenarios_and_live_page(client):
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["ok"] is True
    assert health.json()["provider"] == "mock"
    scenarios = client.get("/v1/scenarios")
    assert scenarios.status_code == 200
    assert {row["id"] for row in scenarios.json()} >= {
        "refund-stalled",
        "email-vendor",
        "dns-cutover",
    }
    page = client.get("/")
    assert page.status_code == 200
    assert "Approval Gate" in page.text


def test_json_decision_and_idempotency_key(client):
    created = client.post("/v1/runs", json={"scenario_id": "refund-stalled"})
    assert created.status_code == 201
    run_id = created.json()["run_id"]
    gate_id = created.json()["gate"]["gate_id"]
    form = client.get(f"/v1/gates/{gate_id}/form")
    assert form.status_code == 200
    assert "issue_refund" in form.text

    approved = client.post(
        f"/v1/runs/{run_id}/decisions",
        json={"decision": "approve", "actor": "ops.reviewer", "idempotency_key": "abc"},
    )
    assert approved.status_code == 200
    assert approved.json()["idempotent_replay"] is False
    assert approved.json()["run"]["tool_execution_count"] == 1

    conflict = client.post(
        f"/v1/gates/{gate_id}/decisions",
        json={
            "decision": "deny",
            "actor": "ops.reviewer",
            "reason": "Changed my mind about this refund.",
            "idempotency_key": "abc",
        },
    )
    assert conflict.status_code == 409
    assert "abc" in conflict.json()["message"]
    assert client.get(f"/v1/runs/{run_id}").json()["tool_execution_count"] == 1


def test_slack_payload_approves_once(client):
    created = client.post("/v1/runs", json={"scenario_id": "dns-cutover"})
    gate_id = created.json()["gate"]["gate_id"]
    payload = {
        "type": "block_actions",
        "user": {"id": "U_OPS", "username": "ops.reviewer"},
        "actions": [
            {
                "action_id": "gate_approve",
                "value": json.dumps({"gate_id": gate_id, "decision": "approve"}),
            }
        ],
    }
    first = client.post("/v1/hooks/slack", data={"payload": json.dumps(payload)})
    assert first.status_code == 200
    assert "203.0.113.24" in first.json()["text"]
    second = client.post("/v1/hooks/slack", data={"payload": json.dumps(payload)})
    assert second.status_code == 200
    assert "Already recorded" in second.json()["text"]
    assert "not called again" in second.json()["text"]
    listed = client.get("/v1/runs")
    assert listed.status_code == 200
    match = next(row for row in listed.json() if row["gate_id"] == gate_id)
    full = client.get(f"/v1/runs/{match['run_id']}")
    assert full.json()["tool_execution_count"] == 1


def test_form_deny_escapes_html(client):
    created = client.post("/v1/runs", json={"scenario_id": "email-vendor"})
    gate_id = created.json()["gate"]["gate_id"]
    reason = "<script>alert(1)</script>"
    response = client.post(
        f"/v1/gates/{gate_id}/form",
        data={"decision": "deny", "actor": "ops.reviewer", "reason": reason},
    )
    assert response.status_code == 200
    assert "<script>" not in response.text
    assert "&lt;script&gt;" in response.text
    assert "Denied" in response.text
    again = client.post(
        f"/v1/gates/{gate_id}/form",
        data={"decision": "deny", "actor": "ops.reviewer", "reason": reason},
    )
    assert again.status_code == 200
    assert "Already recorded" in again.text
