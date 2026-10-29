window.HL_RUNS = {
  "product": "agent-approval-gate",
  "org": "Houghton Labs",
  "generated_at": "2026-10-28T15:00:00Z",
  "clock": "frozen",
  "provider": "mock",
  "note": "Synthetic recording of Northwind Field Goods. This page replays these branches and does not call a server.",
  "runs": [
    {
      "id": "refund-stalled",
      "title": "Refund a stalled shipment",
      "summary": "Full refund of NW-18442, then a second Approve click.",
      "lesson": "Approve, and a duplicate click does not pay twice",
      "risk_label": "Moves money",
      "tool": "issue_refund",
      "task": "Order NW-18442 (queen wool blanket, oat, $86.40) never received a carrier scan from Northline Freight, tracking NL-00018442. Refund the full captured amount. Reason: carrier never scanned the shipment.",
      "feature_expiry": false,
      "has_edit": false,
      "steps_before": [
        {
          "kind": "user",
          "event": "run.started",
          "title": "Task",
          "body": "Order NW-18442 (queen wool blanket, oat, $86.40) never received a carrier scan from Northline Freight, tracking NL-00018442. Refund the full captured amount. Reason: carrier never scanned the shipment.",
          "at": "2026-10-28T15:00:00Z"
        },
        {
          "kind": "model",
          "event": "model.drafted",
          "title": "Drafted a tool call",
          "body": "Order NW-18442 is $86.40 and the carrier never scanned it. I will ask for approval before issuing the full refund.",
          "at": "2026-10-28T15:00:00Z",
          "code": "{\n  \"tool\": \"issue_refund\",\n  \"arguments\": {\n    \"amount_usd\": \"86.40\",\n    \"order_id\": \"NW-18442\",\n    \"reason\": \"Carrier never scanned the shipment.\"\n  }\n}"
        },
        {
          "kind": "persist",
          "event": "gate.opened",
          "title": "Serialized state and paused",
          "body": "Wrote 1575 bytes of agent state to SQLite and opened gate_refund-stalled. resume_cursor is execute_tool. The worker can exit here.",
          "at": "2026-10-28T15:00:00Z",
          "code": "{\n  \"created_at\": \"2026-10-28T15:00:00Z\",\n  \"denial_reason\": null,\n  \"error\": null,\n  \"final_answer\": null,\n  \"gate_id\": \"gate_refund-stalled\",\n  \"messages\": [\n    {\n      \"content\": \"You are the operations agent for Northwind Field Goods, a fictional mail-order company used as a demo. Act only through the provided tools. Use only ids, amounts, and addresses that appear in the task or the tool results. Do not invent personal data. When a tool is high-stakes, still propose exactly one tool call; a human gate will pause it. After a tool result, reply with one short factual sentence and do not call another tool.\",\n      \"role\": \"system\",\n      \"tool_call\": null,\n      \"tool_name\": null\n    },\n    {\n      \"content\": \"Order NW-18442 (queen wool blanket, oat, $86.40) never received a carrier scan from Northline Freight, tracking NL-00018442. Refund the full captured amount. Reason: carrier never scanned the shipment.\",\n      \"role\": \"user\",\n      \"tool_call\": null,\n      \"tool_name\": null\n    },\n    {\n      \"content\": \"Order NW-18442 is $86.40 and the carrier never scanned it. I will ask for approval before issuing the full refund.\",\n      \"role\": \"assistant\",\n      \"tool_call\": {\n        \"arguments\": {\n          \"amount_usd\": \"86.40\",\n          \"order_id\": \"NW-18442\",\n          \"reason\": \"Carrier never scanned the shipment.\"\n        },\n        \"id\": \"call_refund-stalled\",\n        \"name\": \"issue_refund\"\n      },\n      \"tool_name\": null\n    }\n  ],\n  \"pending_call\": {\n    \"arguments\": {\n      \"amount_usd\": \"86.40\",\n      \"order_id\": \"NW-18442\",\n      \"reason\": \"Carrier never scanned the shipment.\"\n    },\n    \"id\": \"call_refund-stalled\",\n    \"name\": \"issue_refund\"\n  },\n  \"resume_cursor\": \"execute_tool\",\n  \"run_id\": \"run_refund-stalled\",\n  \"scenario_id\": \"refund-stalled\",\n  \"status\": \"awaiting_approval\",\n  \"tool_result\": null,\n  \"updated_at\": \"2026-10-28T15:00:00Z\"\n}",
          "collapse": true
        }
      ],
      "proposal": {
        "gate_id": "gate_refund-stalled",
        "run_id": "run_refund-stalled",
        "tool": "issue_refund",
        "risk_label": "Moves money",
        "arguments": {
          "amount_usd": "86.40",
          "order_id": "NW-18442",
          "reason": "Carrier never scanned the shipment."
        },
        "preview": [
          {
            "label": "Order",
            "value": "NW-18442"
          },
          {
            "label": "Amount",
            "value": "$86.40"
          },
          {
            "label": "Captured",
            "value": "$86.40"
          },
          {
            "label": "Reason",
            "value": "Carrier never scanned the shipment."
          }
        ],
        "expires_at": "2026-11-04T15:00:00Z",
        "ttl_label": "7 days",
        "commentary": "Order NW-18442 is $86.40 and the carrier never scanned it. I will ask for approval before issuing the full refund."
      },
      "audit_before": [
        {
          "id": 1,
          "ts": "2026-10-28T15:00:00Z",
          "actor": "agent",
          "event": "run.started",
          "detail": {
            "scenario_id": "refund-stalled"
          },
          "gate_id": null
        },
        {
          "id": 2,
          "ts": "2026-10-28T15:00:00Z",
          "actor": "agent",
          "event": "model.drafted",
          "detail": {
            "arguments": {
              "amount_usd": "86.40",
              "order_id": "NW-18442",
              "reason": "Carrier never scanned the shipment."
            },
            "commentary": "Order NW-18442 is $86.40 and the carrier never scanned it. I will ask for approval before issuing the full refund.",
            "tool": "issue_refund"
          },
          "gate_id": "gate_refund-stalled"
        },
        {
          "id": 3,
          "ts": "2026-10-28T15:00:00Z",
          "actor": "agent",
          "event": "gate.opened",
          "detail": {
            "arguments": {
              "amount_usd": "86.40",
              "order_id": "NW-18442",
              "reason": "Carrier never scanned the shipment."
            },
            "expires_at": "2026-11-04T15:00:00Z",
            "gate_id": "gate_refund-stalled",
            "resume_cursor": "execute_tool",
            "tool": "issue_refund"
          },
          "gate_id": "gate_refund-stalled"
        }
      ],
      "state_bytes": 1575,
      "continuations": {
        "approve": {
          "actor": "ops.reviewer",
          "reason": null,
          "edited_arguments": null,
          "preview": [
            {
              "label": "Order",
              "value": "NW-18442"
            },
            {
              "label": "Amount",
              "value": "$86.40"
            },
            {
              "label": "Captured",
              "value": "$86.40"
            },
            {
              "label": "Reason",
              "value": "Carrier never scanned the shipment."
            }
          ],
          "status": "completed",
          "final_answer": "Issued refund RF-F3D2A7F6 for $86.40 on order NW-18442.",
          "result": {
            "amount_usd": "86.40",
            "ok": true,
            "order_id": "NW-18442",
            "reason": "Carrier never scanned the shipment.",
            "refund_id": "RF-F3D2A7F6",
            "status": "issued",
            "tool": "issue_refund"
          },
          "execution_count": 1,
          "idempotent_replays": 1,
          "steps": [
            {
              "kind": "human",
              "event": "decision.approved",
              "title": "Approved by ops.reviewer",
              "body": "The gate was claimed in one transaction. An identical later click does not run the tool.",
              "at": "2026-10-28T15:00:30Z"
            },
            {
              "kind": "tool",
              "event": "tool.executed",
              "title": "issue_refund executed once",
              "body": "Issued refund RF-F3D2A7F6 for $86.40 on order NW-18442.",
              "at": "2026-10-28T15:00:30Z",
              "code": "{\n  \"amount_usd\": \"86.40\",\n  \"ok\": true,\n  \"order_id\": \"NW-18442\",\n  \"reason\": \"Carrier never scanned the shipment.\",\n  \"refund_id\": \"RF-F3D2A7F6\",\n  \"status\": \"issued\",\n  \"tool\": \"issue_refund\"\n}"
            },
            {
              "kind": "done",
              "event": "run.completed",
              "title": "Run completed",
              "body": "Issued refund RF-F3D2A7F6 for $86.40 on order NW-18442.",
              "at": "2026-10-28T15:00:30Z"
            },
            {
              "kind": "warn",
              "event": "decision.replayed",
              "title": "Duplicate click ignored",
              "body": "Same decision, already stored. tool.executed was not written again.",
              "at": "2026-10-28T15:00:35Z"
            }
          ],
          "audit": [
            {
              "id": 4,
              "ts": "2026-10-28T15:00:30Z",
              "actor": "ops.reviewer",
              "event": "decision.approved",
              "detail": {
                "authorized_arguments": {
                  "amount_usd": "86.40",
                  "order_id": "NW-18442",
                  "reason": "Carrier never scanned the shipment."
                },
                "proposed_arguments": {
                  "amount_usd": "86.40",
                  "order_id": "NW-18442",
                  "reason": "Carrier never scanned the shipment."
                },
                "reason": null
              },
              "gate_id": "gate_refund-stalled"
            },
            {
              "id": 5,
              "ts": "2026-10-28T15:00:30Z",
              "actor": "agent",
              "event": "tool.executed",
              "detail": {
                "effect_id": "RF-F3D2A7F6",
                "result": {
                  "amount_usd": "86.40",
                  "ok": true,
                  "order_id": "NW-18442",
                  "reason": "Carrier never scanned the shipment.",
                  "refund_id": "RF-F3D2A7F6",
                  "status": "issued",
                  "tool": "issue_refund"
                }
              },
              "gate_id": "gate_refund-stalled"
            },
            {
              "id": 6,
              "ts": "2026-10-28T15:00:30Z",
              "actor": "agent",
              "event": "run.completed",
              "detail": {
                "final_answer": "Issued refund RF-F3D2A7F6 for $86.40 on order NW-18442."
              },
              "gate_id": "gate_refund-stalled"
            },
            {
              "id": 7,
              "ts": "2026-10-28T15:00:35Z",
              "actor": "ops.reviewer",
              "event": "decision.replayed",
              "detail": {
                "decision": "approve",
                "idempotency_key": null
              },
              "gate_id": "gate_refund-stalled"
            }
          ]
        },
        "deny": {
          "actor": "ops.reviewer",
          "reason": "Carrier trace is still open. Do not refund the full capture yet.",
          "edited_arguments": null,
          "preview": [
            {
              "label": "Order",
              "value": "NW-18442"
            },
            {
              "label": "Amount",
              "value": "$86.40"
            },
            {
              "label": "Captured",
              "value": "$86.40"
            },
            {
              "label": "Reason",
              "value": "Carrier never scanned the shipment."
            }
          ],
          "status": "denied",
          "final_answer": null,
          "result": null,
          "execution_count": 0,
          "idempotent_replays": 0,
          "steps": [
            {
              "kind": "human",
              "event": "decision.denied",
              "title": "Denied by ops.reviewer",
              "body": "Carrier trace is still open. Do not refund the full capture yet.",
              "at": "2026-10-28T15:00:45Z"
            },
            {
              "kind": "stop",
              "event": "run.denied",
              "title": "Stopped",
              "body": "The tool was not called.",
              "at": "2026-10-28T15:00:45Z"
            }
          ],
          "audit": [
            {
              "id": 4,
              "ts": "2026-10-28T15:00:45Z",
              "actor": "ops.reviewer",
              "event": "decision.denied",
              "detail": {
                "reason": "Carrier trace is still open. Do not refund the full capture yet."
              },
              "gate_id": "gate_refund-stalled"
            },
            {
              "id": 5,
              "ts": "2026-10-28T15:00:45Z",
              "actor": "agent",
              "event": "run.denied",
              "detail": {
                "reason": "Carrier trace is still open. Do not refund the full capture yet."
              },
              "gate_id": "gate_refund-stalled"
            }
          ]
        },
        "edit": null,
        "late": {
          "actor": "ops.reviewer",
          "reason": null,
          "edited_arguments": null,
          "preview": [
            {
              "label": "Order",
              "value": "NW-18442"
            },
            {
              "label": "Amount",
              "value": "$86.40"
            },
            {
              "label": "Captured",
              "value": "$86.40"
            },
            {
              "label": "Reason",
              "value": "Carrier never scanned the shipment."
            }
          ],
          "status": "expired",
          "final_answer": null,
          "result": null,
          "execution_count": 0,
          "idempotent_replays": 0,
          "steps": [
            {
              "kind": "warn",
              "event": "gate.expired",
              "title": "Gate expired",
              "body": "expires_at 2026-11-04T15:00:00Z had passed. Nothing was executed.",
              "at": "2026-11-04T15:00:01Z"
            },
            {
              "kind": "stop",
              "event": "decision.rejected_expired",
              "title": "Late decision rejected",
              "body": "ops.reviewer sent approve after expiry.",
              "at": "2026-11-04T15:00:01Z"
            }
          ],
          "audit": [
            {
              "id": 4,
              "ts": "2026-11-04T15:00:01Z",
              "actor": "clock",
              "event": "gate.expired",
              "detail": {
                "expires_at": "2026-11-04T15:00:00Z"
              },
              "gate_id": "gate_refund-stalled"
            },
            {
              "id": 5,
              "ts": "2026-11-04T15:00:01Z",
              "actor": "ops.reviewer",
              "event": "decision.rejected_expired",
              "detail": {
                "decision": "approve"
              },
              "gate_id": "gate_refund-stalled"
            }
          ]
        }
      }
    },
    {
      "id": "refund-goodwill",
      "title": "Cut a refund in half",
      "summary": "The agent proposes $86.40. A reviewer authorizes $43.20.",
      "lesson": "An edit is re-validated, then executed once",
      "risk_label": "Moves money",
      "tool": "issue_refund",
      "task": "Order NW-18442 is $86.40 and still unscanned. Propose the full refund. A reviewer may reduce it to a partial goodwill amount if they want the carrier trace to finish.",
      "feature_expiry": false,
      "has_edit": true,
      "steps_before": [
        {
          "kind": "user",
          "event": "run.started",
          "title": "Task",
          "body": "Order NW-18442 is $86.40 and still unscanned. Propose the full refund. A reviewer may reduce it to a partial goodwill amount if they want the carrier trace to finish.",
          "at": "2026-10-28T15:00:00Z"
        },
        {
          "kind": "model",
          "event": "model.drafted",
          "title": "Drafted a tool call",
          "body": "The task asks for the full capture on NW-18442. I will propose $86.40 and leave the amount editable.",
          "at": "2026-10-28T15:00:00Z",
          "code": "{\n  \"tool\": \"issue_refund\",\n  \"arguments\": {\n    \"amount_usd\": \"86.40\",\n    \"order_id\": \"NW-18442\",\n    \"reason\": \"Carrier never scanned the shipment.\"\n  }\n}"
        },
        {
          "kind": "persist",
          "event": "gate.opened",
          "title": "Serialized state and paused",
          "body": "Wrote 1531 bytes of agent state to SQLite and opened gate_refund-goodwill. resume_cursor is execute_tool. The worker can exit here.",
          "at": "2026-10-28T15:00:00Z",
          "code": "{\n  \"created_at\": \"2026-10-28T15:00:00Z\",\n  \"denial_reason\": null,\n  \"error\": null,\n  \"final_answer\": null,\n  \"gate_id\": \"gate_refund-goodwill\",\n  \"messages\": [\n    {\n      \"content\": \"You are the operations agent for Northwind Field Goods, a fictional mail-order company used as a demo. Act only through the provided tools. Use only ids, amounts, and addresses that appear in the task or the tool results. Do not invent personal data. When a tool is high-stakes, still propose exactly one tool call; a human gate will pause it. After a tool result, reply with one short factual sentence and do not call another tool.\",\n      \"role\": \"system\",\n      \"tool_call\": null,\n      \"tool_name\": null\n    },\n    {\n      \"content\": \"Order NW-18442 is $86.40 and still unscanned. Propose the full refund. A reviewer may reduce it to a partial goodwill amount if they want the carrier trace to finish.\",\n      \"role\": \"user\",\n      \"tool_call\": null,\n      \"tool_name\": null\n    },\n    {\n      \"content\": \"The task asks for the full capture on NW-18442. I will propose $86.40 and leave the amount editable.\",\n      \"role\": \"assistant\",\n      \"tool_call\": {\n        \"arguments\": {\n          \"amount_usd\": \"86.40\",\n          \"order_id\": \"NW-18442\",\n          \"reason\": \"Carrier never scanned the shipment.\"\n        },\n        \"id\": \"call_refund-goodwill\",\n        \"name\": \"issue_refund\"\n      },\n      \"tool_name\": null\n    }\n  ],\n  \"pending_call\": {\n    \"arguments\": {\n      \"amount_usd\": \"86.40\",\n      \"order_id\": \"NW-18442\",\n      \"reason\": \"Carrier never scanned the shipment.\"\n    },\n    \"id\": \"call_refund-goodwill\",\n    \"name\": \"issue_refund\"\n  },\n  \"resume_cursor\": \"execute_tool\",\n  \"run_id\": \"run_refund-goodwill\",\n  \"scenario_id\": \"refund-goodwill\",\n  \"status\": \"awaiting_approval\",\n  \"tool_result\": null,\n  \"updated_at\": \"2026-10-28T15:00:00Z\"\n}",
          "collapse": true
        }
      ],
      "proposal": {
        "gate_id": "gate_refund-goodwill",
        "run_id": "run_refund-goodwill",
        "tool": "issue_refund",
        "risk_label": "Moves money",
        "arguments": {
          "amount_usd": "86.40",
          "order_id": "NW-18442",
          "reason": "Carrier never scanned the shipment."
        },
        "preview": [
          {
            "label": "Order",
            "value": "NW-18442"
          },
          {
            "label": "Amount",
            "value": "$86.40"
          },
          {
            "label": "Captured",
            "value": "$86.40"
          },
          {
            "label": "Reason",
            "value": "Carrier never scanned the shipment."
          }
        ],
        "expires_at": "2026-11-04T15:00:00Z",
        "ttl_label": "7 days",
        "commentary": "The task asks for the full capture on NW-18442. I will propose $86.40 and leave the amount editable."
      },
      "audit_before": [
        {
          "id": 1,
          "ts": "2026-10-28T15:00:00Z",
          "actor": "agent",
          "event": "run.started",
          "detail": {
            "scenario_id": "refund-goodwill"
          },
          "gate_id": null
        },
        {
          "id": 2,
          "ts": "2026-10-28T15:00:00Z",
          "actor": "agent",
          "event": "model.drafted",
          "detail": {
            "arguments": {
              "amount_usd": "86.40",
              "order_id": "NW-18442",
              "reason": "Carrier never scanned the shipment."
            },
            "commentary": "The task asks for the full capture on NW-18442. I will propose $86.40 and leave the amount editable.",
            "tool": "issue_refund"
          },
          "gate_id": "gate_refund-goodwill"
        },
        {
          "id": 3,
          "ts": "2026-10-28T15:00:00Z",
          "actor": "agent",
          "event": "gate.opened",
          "detail": {
            "arguments": {
              "amount_usd": "86.40",
              "order_id": "NW-18442",
              "reason": "Carrier never scanned the shipment."
            },
            "expires_at": "2026-11-04T15:00:00Z",
            "gate_id": "gate_refund-goodwill",
            "resume_cursor": "execute_tool",
            "tool": "issue_refund"
          },
          "gate_id": "gate_refund-goodwill"
        }
      ],
      "state_bytes": 1531,
      "continuations": {
        "approve": {
          "actor": "ops.reviewer",
          "reason": null,
          "edited_arguments": null,
          "preview": [
            {
              "label": "Order",
              "value": "NW-18442"
            },
            {
              "label": "Amount",
              "value": "$86.40"
            },
            {
              "label": "Captured",
              "value": "$86.40"
            },
            {
              "label": "Reason",
              "value": "Carrier never scanned the shipment."
            }
          ],
          "status": "completed",
          "final_answer": "Issued refund RF-BD20FEE3 for $86.40 on order NW-18442.",
          "result": {
            "amount_usd": "86.40",
            "ok": true,
            "order_id": "NW-18442",
            "reason": "Carrier never scanned the shipment.",
            "refund_id": "RF-BD20FEE3",
            "status": "issued",
            "tool": "issue_refund"
          },
          "execution_count": 1,
          "idempotent_replays": 0,
          "steps": [
            {
              "kind": "human",
              "event": "decision.approved",
              "title": "Approved by ops.reviewer",
              "body": "The gate was claimed in one transaction. An identical later click does not run the tool.",
              "at": "2026-10-28T15:00:30Z"
            },
            {
              "kind": "tool",
              "event": "tool.executed",
              "title": "issue_refund executed once",
              "body": "Issued refund RF-BD20FEE3 for $86.40 on order NW-18442.",
              "at": "2026-10-28T15:00:30Z",
              "code": "{\n  \"amount_usd\": \"86.40\",\n  \"ok\": true,\n  \"order_id\": \"NW-18442\",\n  \"reason\": \"Carrier never scanned the shipment.\",\n  \"refund_id\": \"RF-BD20FEE3\",\n  \"status\": \"issued\",\n  \"tool\": \"issue_refund\"\n}"
            },
            {
              "kind": "done",
              "event": "run.completed",
              "title": "Run completed",
              "body": "Issued refund RF-BD20FEE3 for $86.40 on order NW-18442.",
              "at": "2026-10-28T15:00:30Z"
            }
          ],
          "audit": [
            {
              "id": 4,
              "ts": "2026-10-28T15:00:30Z",
              "actor": "ops.reviewer",
              "event": "decision.approved",
              "detail": {
                "authorized_arguments": {
                  "amount_usd": "86.40",
                  "order_id": "NW-18442",
                  "reason": "Carrier never scanned the shipment."
                },
                "proposed_arguments": {
                  "amount_usd": "86.40",
                  "order_id": "NW-18442",
                  "reason": "Carrier never scanned the shipment."
                },
                "reason": null
              },
              "gate_id": "gate_refund-goodwill"
            },
            {
              "id": 5,
              "ts": "2026-10-28T15:00:30Z",
              "actor": "agent",
              "event": "tool.executed",
              "detail": {
                "effect_id": "RF-BD20FEE3",
                "result": {
                  "amount_usd": "86.40",
                  "ok": true,
                  "order_id": "NW-18442",
                  "reason": "Carrier never scanned the shipment.",
                  "refund_id": "RF-BD20FEE3",
                  "status": "issued",
                  "tool": "issue_refund"
                }
              },
              "gate_id": "gate_refund-goodwill"
            },
            {
              "id": 6,
              "ts": "2026-10-28T15:00:30Z",
              "actor": "agent",
              "event": "run.completed",
              "detail": {
                "final_answer": "Issued refund RF-BD20FEE3 for $86.40 on order NW-18442."
              },
              "gate_id": "gate_refund-goodwill"
            }
          ]
        },
        "deny": {
          "actor": "ops.reviewer",
          "reason": "Do not refund this order.",
          "edited_arguments": null,
          "preview": [
            {
              "label": "Order",
              "value": "NW-18442"
            },
            {
              "label": "Amount",
              "value": "$86.40"
            },
            {
              "label": "Captured",
              "value": "$86.40"
            },
            {
              "label": "Reason",
              "value": "Carrier never scanned the shipment."
            }
          ],
          "status": "denied",
          "final_answer": null,
          "result": null,
          "execution_count": 0,
          "idempotent_replays": 0,
          "steps": [
            {
              "kind": "human",
              "event": "decision.denied",
              "title": "Denied by ops.reviewer",
              "body": "Do not refund this order.",
              "at": "2026-10-28T15:00:45Z"
            },
            {
              "kind": "stop",
              "event": "run.denied",
              "title": "Stopped",
              "body": "The tool was not called.",
              "at": "2026-10-28T15:00:45Z"
            }
          ],
          "audit": [
            {
              "id": 4,
              "ts": "2026-10-28T15:00:45Z",
              "actor": "ops.reviewer",
              "event": "decision.denied",
              "detail": {
                "reason": "Do not refund this order."
              },
              "gate_id": "gate_refund-goodwill"
            },
            {
              "id": 5,
              "ts": "2026-10-28T15:00:45Z",
              "actor": "agent",
              "event": "run.denied",
              "detail": {
                "reason": "Do not refund this order."
              },
              "gate_id": "gate_refund-goodwill"
            }
          ]
        },
        "edit": {
          "actor": "ops.reviewer",
          "reason": "Reviewer reduced the refund to half while the trace stays open.",
          "edited_arguments": {
            "order_id": "NW-18442",
            "amount_usd": "43.20",
            "reason": "Partial goodwill while the carrier trace stays open."
          },
          "preview": [
            {
              "label": "Order",
              "value": "NW-18442"
            },
            {
              "label": "Amount",
              "value": "$43.20"
            },
            {
              "label": "Captured",
              "value": "$86.40"
            },
            {
              "label": "Reason",
              "value": "Partial goodwill while the carrier trace stays open."
            }
          ],
          "status": "completed",
          "final_answer": "Issued refund RF-F824634B for $43.20 on order NW-18442.",
          "result": {
            "amount_usd": "43.20",
            "ok": true,
            "order_id": "NW-18442",
            "reason": "Partial goodwill while the carrier trace stays open.",
            "refund_id": "RF-F824634B",
            "status": "issued",
            "tool": "issue_refund"
          },
          "execution_count": 1,
          "idempotent_replays": 0,
          "steps": [
            {
              "kind": "human",
              "event": "decision.edited",
              "title": "Edited by ops.reviewer",
              "body": "The new arguments passed the same schema and policy checks as the draft.",
              "at": "2026-10-28T15:00:50Z",
              "code": "{\n  \"amount_usd\": \"43.20\",\n  \"order_id\": \"NW-18442\",\n  \"reason\": \"Partial goodwill while the carrier trace stays open.\"\n}"
            },
            {
              "kind": "tool",
              "event": "tool.executed",
              "title": "issue_refund executed once",
              "body": "Issued refund RF-F824634B for $43.20 on order NW-18442.",
              "at": "2026-10-28T15:00:50Z",
              "code": "{\n  \"amount_usd\": \"43.20\",\n  \"ok\": true,\n  \"order_id\": \"NW-18442\",\n  \"reason\": \"Partial goodwill while the carrier trace stays open.\",\n  \"refund_id\": \"RF-F824634B\",\n  \"status\": \"issued\",\n  \"tool\": \"issue_refund\"\n}"
            },
            {
              "kind": "done",
              "event": "run.completed",
              "title": "Run completed",
              "body": "Issued refund RF-F824634B for $43.20 on order NW-18442.",
              "at": "2026-10-28T15:00:50Z"
            }
          ],
          "audit": [
            {
              "id": 4,
              "ts": "2026-10-28T15:00:50Z",
              "actor": "ops.reviewer",
              "event": "decision.edited",
              "detail": {
                "authorized_arguments": {
                  "amount_usd": "43.20",
                  "order_id": "NW-18442",
                  "reason": "Partial goodwill while the carrier trace stays open."
                },
                "proposed_arguments": {
                  "amount_usd": "86.40",
                  "order_id": "NW-18442",
                  "reason": "Carrier never scanned the shipment."
                },
                "reason": "Reviewer reduced the refund to half while the trace stays open."
              },
              "gate_id": "gate_refund-goodwill"
            },
            {
              "id": 5,
              "ts": "2026-10-28T15:00:50Z",
              "actor": "agent",
              "event": "tool.executed",
              "detail": {
                "effect_id": "RF-F824634B",
                "result": {
                  "amount_usd": "43.20",
                  "ok": true,
                  "order_id": "NW-18442",
                  "reason": "Partial goodwill while the carrier trace stays open.",
                  "refund_id": "RF-F824634B",
                  "status": "issued",
                  "tool": "issue_refund"
                }
              },
              "gate_id": "gate_refund-goodwill"
            },
            {
              "id": 6,
              "ts": "2026-10-28T15:00:50Z",
              "actor": "agent",
              "event": "run.completed",
              "detail": {
                "final_answer": "Issued refund RF-F824634B for $43.20 on order NW-18442."
              },
              "gate_id": "gate_refund-goodwill"
            }
          ]
        },
        "late": {
          "actor": "ops.reviewer",
          "reason": null,
          "edited_arguments": null,
          "preview": [
            {
              "label": "Order",
              "value": "NW-18442"
            },
            {
              "label": "Amount",
              "value": "$86.40"
            },
            {
              "label": "Captured",
              "value": "$86.40"
            },
            {
              "label": "Reason",
              "value": "Carrier never scanned the shipment."
            }
          ],
          "status": "expired",
          "final_answer": null,
          "result": null,
          "execution_count": 0,
          "idempotent_replays": 0,
          "steps": [
            {
              "kind": "warn",
              "event": "gate.expired",
              "title": "Gate expired",
              "body": "expires_at 2026-11-04T15:00:00Z had passed. Nothing was executed.",
              "at": "2026-11-04T15:00:01Z"
            },
            {
              "kind": "stop",
              "event": "decision.rejected_expired",
              "title": "Late decision rejected",
              "body": "ops.reviewer sent approve after expiry.",
              "at": "2026-11-04T15:00:01Z"
            }
          ],
          "audit": [
            {
              "id": 4,
              "ts": "2026-11-04T15:00:01Z",
              "actor": "clock",
              "event": "gate.expired",
              "detail": {
                "expires_at": "2026-11-04T15:00:00Z"
              },
              "gate_id": "gate_refund-goodwill"
            },
            {
              "id": 5,
              "ts": "2026-11-04T15:00:01Z",
              "actor": "ops.reviewer",
              "event": "decision.rejected_expired",
              "detail": {
                "decision": "approve"
              },
              "gate_id": "gate_refund-goodwill"
            }
          ]
        }
      }
    },
    {
      "id": "email-vendor",
      "title": "Hold a vendor email",
      "summary": "A hold-check to the vendor desk. The reviewer stops it.",
      "lesson": "Deny records a reason and never calls the tool",
      "risk_label": "Sends mail",
      "tool": "send_email",
      "task": "Email vendor-desk@northwind.example about invoice INV-2091 (PO-441, wool blankets). Ask them to confirm it is still on hold. Do not promise a payment date.",
      "feature_expiry": false,
      "has_edit": false,
      "steps_before": [
        {
          "kind": "user",
          "event": "run.started",
          "title": "Task",
          "body": "Email vendor-desk@northwind.example about invoice INV-2091 (PO-441, wool blankets). Ask them to confirm it is still on hold. Do not promise a payment date.",
          "at": "2026-10-28T15:00:00Z"
        },
        {
          "kind": "model",
          "event": "model.drafted",
          "title": "Drafted a tool call",
          "body": "This note only confirms the hold on INV-2091. It goes to the vendor desk, and it promises no payment date.",
          "at": "2026-10-28T15:00:00Z",
          "code": "{\n  \"tool\": \"send_email\",\n  \"arguments\": {\n    \"body\": \"Please confirm invoice INV-2091 (PO-441, wool blankets) is still on hold. No payment date is promised in this note.\",\n    \"subject\": \"INV-2091 hold check\",\n    \"to\": \"vendor-desk@northwind.example\"\n  }\n}"
        },
        {
          "kind": "persist",
          "event": "gate.opened",
          "title": "Serialized state and paused",
          "body": "Wrote 1715 bytes of agent state to SQLite and opened gate_email-vendor. resume_cursor is execute_tool. The worker can exit here.",
          "at": "2026-10-28T15:00:00Z",
          "code": "{\n  \"created_at\": \"2026-10-28T15:00:00Z\",\n  \"denial_reason\": null,\n  \"error\": null,\n  \"final_answer\": null,\n  \"gate_id\": \"gate_email-vendor\",\n  \"messages\": [\n    {\n      \"content\": \"You are the operations agent for Northwind Field Goods, a fictional mail-order company used as a demo. Act only through the provided tools. Use only ids, amounts, and addresses that appear in the task or the tool results. Do not invent personal data. When a tool is high-stakes, still propose exactly one tool call; a human gate will pause it. After a tool result, reply with one short factual sentence and do not call another tool.\",\n      \"role\": \"system\",\n      \"tool_call\": null,\n      \"tool_name\": null\n    },\n    {\n      \"content\": \"Email vendor-desk@northwind.example about invoice INV-2091 (PO-441, wool blankets). Ask them to confirm it is still on hold. Do not promise a payment date.\",\n      \"role\": \"user\",\n      \"tool_call\": null,\n      \"tool_name\": null\n    },\n    {\n      \"content\": \"This note only confirms the hold on INV-2091. It goes to the vendor desk, and it promises no payment date.\",\n      \"role\": \"assistant\",\n      \"tool_call\": {\n        \"arguments\": {\n          \"body\": \"Please confirm invoice INV-2091 (PO-441, wool blankets) is still on hold. No payment date is promised in this note.\",\n          \"subject\": \"INV-2091 hold check\",\n          \"to\": \"vendor-desk@northwind.example\"\n        },\n        \"id\": \"call_email-vendor\",\n        \"name\": \"send_email\"\n      },\n      \"tool_name\": null\n    }\n  ],\n  \"pending_call\": {\n    \"arguments\": {\n      \"body\": \"Please confirm invoice INV-2091 (PO-441, wool blankets) is still on hold. No payment date is promised in this note.\",\n      \"subject\": \"INV-2091 hold check\",\n      \"to\": \"vendor-desk@northwind.example\"\n    },\n    \"id\": \"call_email-vendor\",\n    \"name\": \"send_email\"\n  },\n  \"resume_cursor\": \"execute_tool\",\n  \"run_id\": \"run_email-vendor\",\n  \"scenario_id\": \"email-vendor\",\n  \"status\": \"awaiting_approval\",\n  \"tool_result\": null,\n  \"updated_at\": \"2026-10-28T15:00:00Z\"\n}",
          "collapse": true
        }
      ],
      "proposal": {
        "gate_id": "gate_email-vendor",
        "run_id": "run_email-vendor",
        "tool": "send_email",
        "risk_label": "Sends mail",
        "arguments": {
          "body": "Please confirm invoice INV-2091 (PO-441, wool blankets) is still on hold. No payment date is promised in this note.",
          "subject": "INV-2091 hold check",
          "to": "vendor-desk@northwind.example"
        },
        "preview": [
          {
            "label": "To",
            "value": "vendor-desk@northwind.example"
          },
          {
            "label": "Subject",
            "value": "INV-2091 hold check"
          },
          {
            "label": "Body",
            "value": "Please confirm invoice INV-2091 (PO-441, wool blankets) is still on hold. No payment date is promised in this note."
          }
        ],
        "expires_at": "2026-10-31T15:00:00Z",
        "ttl_label": "3 days",
        "commentary": "This note only confirms the hold on INV-2091. It goes to the vendor desk, and it promises no payment date."
      },
      "audit_before": [
        {
          "id": 1,
          "ts": "2026-10-28T15:00:00Z",
          "actor": "agent",
          "event": "run.started",
          "detail": {
            "scenario_id": "email-vendor"
          },
          "gate_id": null
        },
        {
          "id": 2,
          "ts": "2026-10-28T15:00:00Z",
          "actor": "agent",
          "event": "model.drafted",
          "detail": {
            "arguments": {
              "body": "Please confirm invoice INV-2091 (PO-441, wool blankets) is still on hold. No payment date is promised in this note.",
              "subject": "INV-2091 hold check",
              "to": "vendor-desk@northwind.example"
            },
            "commentary": "This note only confirms the hold on INV-2091. It goes to the vendor desk, and it promises no payment date.",
            "tool": "send_email"
          },
          "gate_id": "gate_email-vendor"
        },
        {
          "id": 3,
          "ts": "2026-10-28T15:00:00Z",
          "actor": "agent",
          "event": "gate.opened",
          "detail": {
            "arguments": {
              "body": "Please confirm invoice INV-2091 (PO-441, wool blankets) is still on hold. No payment date is promised in this note.",
              "subject": "INV-2091 hold check",
              "to": "vendor-desk@northwind.example"
            },
            "expires_at": "2026-10-31T15:00:00Z",
            "gate_id": "gate_email-vendor",
            "resume_cursor": "execute_tool",
            "tool": "send_email"
          },
          "gate_id": "gate_email-vendor"
        }
      ],
      "state_bytes": 1715,
      "continuations": {
        "approve": {
          "actor": "ops.reviewer",
          "reason": null,
          "edited_arguments": null,
          "preview": [
            {
              "label": "To",
              "value": "vendor-desk@northwind.example"
            },
            {
              "label": "Subject",
              "value": "INV-2091 hold check"
            },
            {
              "label": "Body",
              "value": "Please confirm invoice INV-2091 (PO-441, wool blankets) is still on hold. No payment date is promised in this note."
            }
          ],
          "status": "completed",
          "final_answer": "Queued MSG-D981D892 to vendor-desk@northwind.example.",
          "result": {
            "message_id": "MSG-D981D892",
            "ok": true,
            "status": "queued",
            "subject": "INV-2091 hold check",
            "to": "vendor-desk@northwind.example",
            "tool": "send_email"
          },
          "execution_count": 1,
          "idempotent_replays": 0,
          "steps": [
            {
              "kind": "human",
              "event": "decision.approved",
              "title": "Approved by ops.reviewer",
              "body": "The gate was claimed in one transaction. An identical later click does not run the tool.",
              "at": "2026-10-28T15:00:30Z"
            },
            {
              "kind": "tool",
              "event": "tool.executed",
              "title": "send_email executed once",
              "body": "Queued MSG-D981D892 to vendor-desk@northwind.example.",
              "at": "2026-10-28T15:00:30Z",
              "code": "{\n  \"message_id\": \"MSG-D981D892\",\n  \"ok\": true,\n  \"status\": \"queued\",\n  \"subject\": \"INV-2091 hold check\",\n  \"to\": \"vendor-desk@northwind.example\",\n  \"tool\": \"send_email\"\n}"
            },
            {
              "kind": "done",
              "event": "run.completed",
              "title": "Run completed",
              "body": "Queued MSG-D981D892 to vendor-desk@northwind.example.",
              "at": "2026-10-28T15:00:30Z"
            }
          ],
          "audit": [
            {
              "id": 4,
              "ts": "2026-10-28T15:00:30Z",
              "actor": "ops.reviewer",
              "event": "decision.approved",
              "detail": {
                "authorized_arguments": {
                  "body": "Please confirm invoice INV-2091 (PO-441, wool blankets) is still on hold. No payment date is promised in this note.",
                  "subject": "INV-2091 hold check",
                  "to": "vendor-desk@northwind.example"
                },
                "proposed_arguments": {
                  "body": "Please confirm invoice INV-2091 (PO-441, wool blankets) is still on hold. No payment date is promised in this note.",
                  "subject": "INV-2091 hold check",
                  "to": "vendor-desk@northwind.example"
                },
                "reason": null
              },
              "gate_id": "gate_email-vendor"
            },
            {
              "id": 5,
              "ts": "2026-10-28T15:00:30Z",
              "actor": "agent",
              "event": "tool.executed",
              "detail": {
                "effect_id": "MSG-D981D892",
                "result": {
                  "message_id": "MSG-D981D892",
                  "ok": true,
                  "status": "queued",
                  "subject": "INV-2091 hold check",
                  "to": "vendor-desk@northwind.example",
                  "tool": "send_email"
                }
              },
              "gate_id": "gate_email-vendor"
            },
            {
              "id": 6,
              "ts": "2026-10-28T15:00:30Z",
              "actor": "agent",
              "event": "run.completed",
              "detail": {
                "final_answer": "Queued MSG-D981D892 to vendor-desk@northwind.example."
              },
              "gate_id": "gate_email-vendor"
            }
          ]
        },
        "deny": {
          "actor": "ops.reviewer",
          "reason": "Finance already has a thread open with the vendor. Do not send another.",
          "edited_arguments": null,
          "preview": [
            {
              "label": "To",
              "value": "vendor-desk@northwind.example"
            },
            {
              "label": "Subject",
              "value": "INV-2091 hold check"
            },
            {
              "label": "Body",
              "value": "Please confirm invoice INV-2091 (PO-441, wool blankets) is still on hold. No payment date is promised in this note."
            }
          ],
          "status": "denied",
          "final_answer": null,
          "result": null,
          "execution_count": 0,
          "idempotent_replays": 0,
          "steps": [
            {
              "kind": "human",
              "event": "decision.denied",
              "title": "Denied by ops.reviewer",
              "body": "Finance already has a thread open with the vendor. Do not send another.",
              "at": "2026-10-28T15:00:45Z"
            },
            {
              "kind": "stop",
              "event": "run.denied",
              "title": "Stopped",
              "body": "The tool was not called.",
              "at": "2026-10-28T15:00:45Z"
            }
          ],
          "audit": [
            {
              "id": 4,
              "ts": "2026-10-28T15:00:45Z",
              "actor": "ops.reviewer",
              "event": "decision.denied",
              "detail": {
                "reason": "Finance already has a thread open with the vendor. Do not send another."
              },
              "gate_id": "gate_email-vendor"
            },
            {
              "id": 5,
              "ts": "2026-10-28T15:00:45Z",
              "actor": "agent",
              "event": "run.denied",
              "detail": {
                "reason": "Finance already has a thread open with the vendor. Do not send another."
              },
              "gate_id": "gate_email-vendor"
            }
          ]
        },
        "edit": null,
        "late": {
          "actor": "ops.reviewer",
          "reason": null,
          "edited_arguments": null,
          "preview": [
            {
              "label": "To",
              "value": "vendor-desk@northwind.example"
            },
            {
              "label": "Subject",
              "value": "INV-2091 hold check"
            },
            {
              "label": "Body",
              "value": "Please confirm invoice INV-2091 (PO-441, wool blankets) is still on hold. No payment date is promised in this note."
            }
          ],
          "status": "expired",
          "final_answer": null,
          "result": null,
          "execution_count": 0,
          "idempotent_replays": 0,
          "steps": [
            {
              "kind": "warn",
              "event": "gate.expired",
              "title": "Gate expired",
              "body": "expires_at 2026-10-31T15:00:00Z had passed. Nothing was executed.",
              "at": "2026-10-31T15:00:01Z"
            },
            {
              "kind": "stop",
              "event": "decision.rejected_expired",
              "title": "Late decision rejected",
              "body": "ops.reviewer sent approve after expiry.",
              "at": "2026-10-31T15:00:01Z"
            }
          ],
          "audit": [
            {
              "id": 4,
              "ts": "2026-10-31T15:00:01Z",
              "actor": "clock",
              "event": "gate.expired",
              "detail": {
                "expires_at": "2026-10-31T15:00:00Z"
              },
              "gate_id": "gate_email-vendor"
            },
            {
              "id": 5,
              "ts": "2026-10-31T15:00:01Z",
              "actor": "ops.reviewer",
              "event": "decision.rejected_expired",
              "detail": {
                "decision": "approve"
              },
              "gate_id": "gate_email-vendor"
            }
          ]
        }
      }
    },
    {
      "id": "dns-cutover",
      "title": "Cut over a DNS record",
      "summary": "Move shop.example.test to 203.0.113.24. Leave status.example.test alone.",
      "lesson": "Approve applies the mock change exactly once",
      "risk_label": "Changes DNS",
      "tool": "change_dns",
      "task": "Change the A record for shop.example.test from 203.0.113.10 to 203.0.113.24 in zone example.test. Do not touch status.example.test.",
      "feature_expiry": false,
      "has_edit": false,
      "steps_before": [
        {
          "kind": "user",
          "event": "run.started",
          "title": "Task",
          "body": "Change the A record for shop.example.test from 203.0.113.10 to 203.0.113.24 in zone example.test. Do not touch status.example.test.",
          "at": "2026-10-28T15:00:00Z"
        },
        {
          "kind": "model",
          "event": "model.drafted",
          "title": "Drafted a tool call",
          "body": "shop.example.test should move from 203.0.113.10 to 203.0.113.24. status.example.test stays as it is.",
          "at": "2026-10-28T15:00:00Z",
          "code": "{\n  \"tool\": \"change_dns\",\n  \"arguments\": {\n    \"name\": \"shop.example.test\",\n    \"record_type\": \"A\",\n    \"value\": \"203.0.113.24\",\n    \"zone\": \"example.test\"\n  }\n}"
        },
        {
          "kind": "persist",
          "event": "gate.opened",
          "title": "Serialized state and paused",
          "body": "Wrote 1472 bytes of agent state to SQLite and opened gate_dns-cutover. resume_cursor is execute_tool. The worker can exit here.",
          "at": "2026-10-28T15:00:00Z",
          "code": "{\n  \"created_at\": \"2026-10-28T15:00:00Z\",\n  \"denial_reason\": null,\n  \"error\": null,\n  \"final_answer\": null,\n  \"gate_id\": \"gate_dns-cutover\",\n  \"messages\": [\n    {\n      \"content\": \"You are the operations agent for Northwind Field Goods, a fictional mail-order company used as a demo. Act only through the provided tools. Use only ids, amounts, and addresses that appear in the task or the tool results. Do not invent personal data. When a tool is high-stakes, still propose exactly one tool call; a human gate will pause it. After a tool result, reply with one short factual sentence and do not call another tool.\",\n      \"role\": \"system\",\n      \"tool_call\": null,\n      \"tool_name\": null\n    },\n    {\n      \"content\": \"Change the A record for shop.example.test from 203.0.113.10 to 203.0.113.24 in zone example.test. Do not touch status.example.test.\",\n      \"role\": \"user\",\n      \"tool_call\": null,\n      \"tool_name\": null\n    },\n    {\n      \"content\": \"shop.example.test should move from 203.0.113.10 to 203.0.113.24. status.example.test stays as it is.\",\n      \"role\": \"assistant\",\n      \"tool_call\": {\n        \"arguments\": {\n          \"name\": \"shop.example.test\",\n          \"record_type\": \"A\",\n          \"value\": \"203.0.113.24\",\n          \"zone\": \"example.test\"\n        },\n        \"id\": \"call_dns-cutover\",\n        \"name\": \"change_dns\"\n      },\n      \"tool_name\": null\n    }\n  ],\n  \"pending_call\": {\n    \"arguments\": {\n      \"name\": \"shop.example.test\",\n      \"record_type\": \"A\",\n      \"value\": \"203.0.113.24\",\n      \"zone\": \"example.test\"\n    },\n    \"id\": \"call_dns-cutover\",\n    \"name\": \"change_dns\"\n  },\n  \"resume_cursor\": \"execute_tool\",\n  \"run_id\": \"run_dns-cutover\",\n  \"scenario_id\": \"dns-cutover\",\n  \"status\": \"awaiting_approval\",\n  \"tool_result\": null,\n  \"updated_at\": \"2026-10-28T15:00:00Z\"\n}",
          "collapse": true
        }
      ],
      "proposal": {
        "gate_id": "gate_dns-cutover",
        "run_id": "run_dns-cutover",
        "tool": "change_dns",
        "risk_label": "Changes DNS",
        "arguments": {
          "name": "shop.example.test",
          "record_type": "A",
          "value": "203.0.113.24",
          "zone": "example.test"
        },
        "preview": [
          {
            "label": "Record",
            "value": "shop.example.test"
          },
          {
            "label": "Type",
            "value": "A"
          },
          {
            "label": "From",
            "value": "203.0.113.10"
          },
          {
            "label": "To",
            "value": "203.0.113.24"
          }
        ],
        "expires_at": "2026-10-28T19:00:00Z",
        "ttl_label": "4 hours",
        "commentary": "shop.example.test should move from 203.0.113.10 to 203.0.113.24. status.example.test stays as it is."
      },
      "audit_before": [
        {
          "id": 1,
          "ts": "2026-10-28T15:00:00Z",
          "actor": "agent",
          "event": "run.started",
          "detail": {
            "scenario_id": "dns-cutover"
          },
          "gate_id": null
        },
        {
          "id": 2,
          "ts": "2026-10-28T15:00:00Z",
          "actor": "agent",
          "event": "model.drafted",
          "detail": {
            "arguments": {
              "name": "shop.example.test",
              "record_type": "A",
              "value": "203.0.113.24",
              "zone": "example.test"
            },
            "commentary": "shop.example.test should move from 203.0.113.10 to 203.0.113.24. status.example.test stays as it is.",
            "tool": "change_dns"
          },
          "gate_id": "gate_dns-cutover"
        },
        {
          "id": 3,
          "ts": "2026-10-28T15:00:00Z",
          "actor": "agent",
          "event": "gate.opened",
          "detail": {
            "arguments": {
              "name": "shop.example.test",
              "record_type": "A",
              "value": "203.0.113.24",
              "zone": "example.test"
            },
            "expires_at": "2026-10-28T19:00:00Z",
            "gate_id": "gate_dns-cutover",
            "resume_cursor": "execute_tool",
            "tool": "change_dns"
          },
          "gate_id": "gate_dns-cutover"
        }
      ],
      "state_bytes": 1472,
      "continuations": {
        "approve": {
          "actor": "ops.reviewer",
          "reason": null,
          "edited_arguments": null,
          "preview": [
            {
              "label": "Record",
              "value": "shop.example.test"
            },
            {
              "label": "Type",
              "value": "A"
            },
            {
              "label": "From",
              "value": "203.0.113.10"
            },
            {
              "label": "To",
              "value": "203.0.113.24"
            }
          ],
          "status": "completed",
          "final_answer": "Updated shop.example.test from 203.0.113.10 to 203.0.113.24 (DNS-F549D43B).",
          "result": {
            "change_id": "DNS-F549D43B",
            "name": "shop.example.test",
            "ok": true,
            "previous": "203.0.113.10",
            "record_type": "A",
            "status": "applied",
            "tool": "change_dns",
            "value": "203.0.113.24",
            "zone": "example.test"
          },
          "execution_count": 1,
          "idempotent_replays": 0,
          "steps": [
            {
              "kind": "human",
              "event": "decision.approved",
              "title": "Approved by ops.reviewer",
              "body": "The gate was claimed in one transaction. An identical later click does not run the tool.",
              "at": "2026-10-28T15:00:30Z"
            },
            {
              "kind": "tool",
              "event": "tool.executed",
              "title": "change_dns executed once",
              "body": "Updated shop.example.test from 203.0.113.10 to 203.0.113.24 (DNS-F549D43B).",
              "at": "2026-10-28T15:00:30Z",
              "code": "{\n  \"change_id\": \"DNS-F549D43B\",\n  \"name\": \"shop.example.test\",\n  \"ok\": true,\n  \"previous\": \"203.0.113.10\",\n  \"record_type\": \"A\",\n  \"status\": \"applied\",\n  \"tool\": \"change_dns\",\n  \"value\": \"203.0.113.24\",\n  \"zone\": \"example.test\"\n}"
            },
            {
              "kind": "done",
              "event": "run.completed",
              "title": "Run completed",
              "body": "Updated shop.example.test from 203.0.113.10 to 203.0.113.24 (DNS-F549D43B).",
              "at": "2026-10-28T15:00:30Z"
            }
          ],
          "audit": [
            {
              "id": 4,
              "ts": "2026-10-28T15:00:30Z",
              "actor": "ops.reviewer",
              "event": "decision.approved",
              "detail": {
                "authorized_arguments": {
                  "name": "shop.example.test",
                  "record_type": "A",
                  "value": "203.0.113.24",
                  "zone": "example.test"
                },
                "proposed_arguments": {
                  "name": "shop.example.test",
                  "record_type": "A",
                  "value": "203.0.113.24",
                  "zone": "example.test"
                },
                "reason": null
              },
              "gate_id": "gate_dns-cutover"
            },
            {
              "id": 5,
              "ts": "2026-10-28T15:00:30Z",
              "actor": "agent",
              "event": "tool.executed",
              "detail": {
                "effect_id": "DNS-F549D43B",
                "result": {
                  "change_id": "DNS-F549D43B",
                  "name": "shop.example.test",
                  "ok": true,
                  "previous": "203.0.113.10",
                  "record_type": "A",
                  "status": "applied",
                  "tool": "change_dns",
                  "value": "203.0.113.24",
                  "zone": "example.test"
                }
              },
              "gate_id": "gate_dns-cutover"
            },
            {
              "id": 6,
              "ts": "2026-10-28T15:00:30Z",
              "actor": "agent",
              "event": "run.completed",
              "detail": {
                "final_answer": "Updated shop.example.test from 203.0.113.10 to 203.0.113.24 (DNS-F549D43B)."
              },
              "gate_id": "gate_dns-cutover"
            }
          ]
        },
        "deny": {
          "actor": "ops.reviewer",
          "reason": "Change window is frozen until the status name is moved.",
          "edited_arguments": null,
          "preview": [
            {
              "label": "Record",
              "value": "shop.example.test"
            },
            {
              "label": "Type",
              "value": "A"
            },
            {
              "label": "From",
              "value": "203.0.113.10"
            },
            {
              "label": "To",
              "value": "203.0.113.24"
            }
          ],
          "status": "denied",
          "final_answer": null,
          "result": null,
          "execution_count": 0,
          "idempotent_replays": 0,
          "steps": [
            {
              "kind": "human",
              "event": "decision.denied",
              "title": "Denied by ops.reviewer",
              "body": "Change window is frozen until the status name is moved.",
              "at": "2026-10-28T15:00:45Z"
            },
            {
              "kind": "stop",
              "event": "run.denied",
              "title": "Stopped",
              "body": "The tool was not called.",
              "at": "2026-10-28T15:00:45Z"
            }
          ],
          "audit": [
            {
              "id": 4,
              "ts": "2026-10-28T15:00:45Z",
              "actor": "ops.reviewer",
              "event": "decision.denied",
              "detail": {
                "reason": "Change window is frozen until the status name is moved."
              },
              "gate_id": "gate_dns-cutover"
            },
            {
              "id": 5,
              "ts": "2026-10-28T15:00:45Z",
              "actor": "agent",
              "event": "run.denied",
              "detail": {
                "reason": "Change window is frozen until the status name is moved."
              },
              "gate_id": "gate_dns-cutover"
            }
          ]
        },
        "edit": null,
        "late": {
          "actor": "ops.reviewer",
          "reason": null,
          "edited_arguments": null,
          "preview": [
            {
              "label": "Record",
              "value": "shop.example.test"
            },
            {
              "label": "Type",
              "value": "A"
            },
            {
              "label": "From",
              "value": "203.0.113.10"
            },
            {
              "label": "To",
              "value": "203.0.113.24"
            }
          ],
          "status": "expired",
          "final_answer": null,
          "result": null,
          "execution_count": 0,
          "idempotent_replays": 0,
          "steps": [
            {
              "kind": "warn",
              "event": "gate.expired",
              "title": "Gate expired",
              "body": "expires_at 2026-10-28T19:00:00Z had passed. Nothing was executed.",
              "at": "2026-10-28T19:00:01Z"
            },
            {
              "kind": "stop",
              "event": "decision.rejected_expired",
              "title": "Late decision rejected",
              "body": "ops.reviewer sent approve after expiry.",
              "at": "2026-10-28T19:00:01Z"
            }
          ],
          "audit": [
            {
              "id": 4,
              "ts": "2026-10-28T19:00:01Z",
              "actor": "clock",
              "event": "gate.expired",
              "detail": {
                "expires_at": "2026-10-28T19:00:00Z"
              },
              "gate_id": "gate_dns-cutover"
            },
            {
              "id": 5,
              "ts": "2026-10-28T19:00:01Z",
              "actor": "ops.reviewer",
              "event": "decision.rejected_expired",
              "detail": {
                "decision": "approve"
              },
              "gate_id": "gate_dns-cutover"
            }
          ]
        }
      }
    },
    {
      "id": "refund-expired",
      "title": "A refund window closes",
      "summary": "NW-17710 stays open for one hour. A late Approve does not pay.",
      "lesson": "Past expires_at, the tool is not called",
      "risk_label": "Moves money",
      "tool": "issue_refund",
      "task": "Order NW-17710 (linen napkin set, $18.00) was cancelled before it shipped, and the capture is still open. Refund the full $18.00.",
      "feature_expiry": true,
      "has_edit": false,
      "steps_before": [
        {
          "kind": "user",
          "event": "run.started",
          "title": "Task",
          "body": "Order NW-17710 (linen napkin set, $18.00) was cancelled before it shipped, and the capture is still open. Refund the full $18.00.",
          "at": "2026-10-28T15:00:00Z"
        },
        {
          "kind": "model",
          "event": "model.drafted",
          "title": "Drafted a tool call",
          "body": "Order NW-17710 was cancelled before shipment and the $18.00 capture is still open. I will propose that refund.",
          "at": "2026-10-28T15:00:00Z",
          "code": "{\n  \"tool\": \"issue_refund\",\n  \"arguments\": {\n    \"amount_usd\": \"18.00\",\n    \"order_id\": \"NW-17710\",\n    \"reason\": \"Cancelled before shipment; capture still open.\"\n  }\n}"
        },
        {
          "kind": "persist",
          "event": "gate.opened",
          "title": "Serialized state and paused",
          "body": "Wrote 1521 bytes of agent state to SQLite and opened gate_refund-expired. resume_cursor is execute_tool. The worker can exit here.",
          "at": "2026-10-28T15:00:00Z",
          "code": "{\n  \"created_at\": \"2026-10-28T15:00:00Z\",\n  \"denial_reason\": null,\n  \"error\": null,\n  \"final_answer\": null,\n  \"gate_id\": \"gate_refund-expired\",\n  \"messages\": [\n    {\n      \"content\": \"You are the operations agent for Northwind Field Goods, a fictional mail-order company used as a demo. Act only through the provided tools. Use only ids, amounts, and addresses that appear in the task or the tool results. Do not invent personal data. When a tool is high-stakes, still propose exactly one tool call; a human gate will pause it. After a tool result, reply with one short factual sentence and do not call another tool.\",\n      \"role\": \"system\",\n      \"tool_call\": null,\n      \"tool_name\": null\n    },\n    {\n      \"content\": \"Order NW-17710 (linen napkin set, $18.00) was cancelled before it shipped, and the capture is still open. Refund the full $18.00.\",\n      \"role\": \"user\",\n      \"tool_call\": null,\n      \"tool_name\": null\n    },\n    {\n      \"content\": \"Order NW-17710 was cancelled before shipment and the $18.00 capture is still open. I will propose that refund.\",\n      \"role\": \"assistant\",\n      \"tool_call\": {\n        \"arguments\": {\n          \"amount_usd\": \"18.00\",\n          \"order_id\": \"NW-17710\",\n          \"reason\": \"Cancelled before shipment; capture still open.\"\n        },\n        \"id\": \"call_refund-expired\",\n        \"name\": \"issue_refund\"\n      },\n      \"tool_name\": null\n    }\n  ],\n  \"pending_call\": {\n    \"arguments\": {\n      \"amount_usd\": \"18.00\",\n      \"order_id\": \"NW-17710\",\n      \"reason\": \"Cancelled before shipment; capture still open.\"\n    },\n    \"id\": \"call_refund-expired\",\n    \"name\": \"issue_refund\"\n  },\n  \"resume_cursor\": \"execute_tool\",\n  \"run_id\": \"run_refund-expired\",\n  \"scenario_id\": \"refund-expired\",\n  \"status\": \"awaiting_approval\",\n  \"tool_result\": null,\n  \"updated_at\": \"2026-10-28T15:00:00Z\"\n}",
          "collapse": true
        }
      ],
      "proposal": {
        "gate_id": "gate_refund-expired",
        "run_id": "run_refund-expired",
        "tool": "issue_refund",
        "risk_label": "Moves money",
        "arguments": {
          "amount_usd": "18.00",
          "order_id": "NW-17710",
          "reason": "Cancelled before shipment; capture still open."
        },
        "preview": [
          {
            "label": "Order",
            "value": "NW-17710"
          },
          {
            "label": "Amount",
            "value": "$18.00"
          },
          {
            "label": "Captured",
            "value": "$18.00"
          },
          {
            "label": "Reason",
            "value": "Cancelled before shipment; capture still open."
          }
        ],
        "expires_at": "2026-10-28T16:00:00Z",
        "ttl_label": "1 hour",
        "commentary": "Order NW-17710 was cancelled before shipment and the $18.00 capture is still open. I will propose that refund."
      },
      "audit_before": [
        {
          "id": 1,
          "ts": "2026-10-28T15:00:00Z",
          "actor": "agent",
          "event": "run.started",
          "detail": {
            "scenario_id": "refund-expired"
          },
          "gate_id": null
        },
        {
          "id": 2,
          "ts": "2026-10-28T15:00:00Z",
          "actor": "agent",
          "event": "model.drafted",
          "detail": {
            "arguments": {
              "amount_usd": "18.00",
              "order_id": "NW-17710",
              "reason": "Cancelled before shipment; capture still open."
            },
            "commentary": "Order NW-17710 was cancelled before shipment and the $18.00 capture is still open. I will propose that refund.",
            "tool": "issue_refund"
          },
          "gate_id": "gate_refund-expired"
        },
        {
          "id": 3,
          "ts": "2026-10-28T15:00:00Z",
          "actor": "agent",
          "event": "gate.opened",
          "detail": {
            "arguments": {
              "amount_usd": "18.00",
              "order_id": "NW-17710",
              "reason": "Cancelled before shipment; capture still open."
            },
            "expires_at": "2026-10-28T16:00:00Z",
            "gate_id": "gate_refund-expired",
            "resume_cursor": "execute_tool",
            "tool": "issue_refund"
          },
          "gate_id": "gate_refund-expired"
        }
      ],
      "state_bytes": 1521,
      "continuations": {
        "approve": {
          "actor": "ops.reviewer",
          "reason": null,
          "edited_arguments": null,
          "preview": [
            {
              "label": "Order",
              "value": "NW-17710"
            },
            {
              "label": "Amount",
              "value": "$18.00"
            },
            {
              "label": "Captured",
              "value": "$18.00"
            },
            {
              "label": "Reason",
              "value": "Cancelled before shipment; capture still open."
            }
          ],
          "status": "completed",
          "final_answer": "Issued refund RF-5AD94AD2 for $18.00 on order NW-17710.",
          "result": {
            "amount_usd": "18.00",
            "ok": true,
            "order_id": "NW-17710",
            "reason": "Cancelled before shipment; capture still open.",
            "refund_id": "RF-5AD94AD2",
            "status": "issued",
            "tool": "issue_refund"
          },
          "execution_count": 1,
          "idempotent_replays": 0,
          "steps": [
            {
              "kind": "human",
              "event": "decision.approved",
              "title": "Approved by ops.reviewer",
              "body": "The gate was claimed in one transaction. An identical later click does not run the tool.",
              "at": "2026-10-28T15:00:30Z"
            },
            {
              "kind": "tool",
              "event": "tool.executed",
              "title": "issue_refund executed once",
              "body": "Issued refund RF-5AD94AD2 for $18.00 on order NW-17710.",
              "at": "2026-10-28T15:00:30Z",
              "code": "{\n  \"amount_usd\": \"18.00\",\n  \"ok\": true,\n  \"order_id\": \"NW-17710\",\n  \"reason\": \"Cancelled before shipment; capture still open.\",\n  \"refund_id\": \"RF-5AD94AD2\",\n  \"status\": \"issued\",\n  \"tool\": \"issue_refund\"\n}"
            },
            {
              "kind": "done",
              "event": "run.completed",
              "title": "Run completed",
              "body": "Issued refund RF-5AD94AD2 for $18.00 on order NW-17710.",
              "at": "2026-10-28T15:00:30Z"
            }
          ],
          "audit": [
            {
              "id": 4,
              "ts": "2026-10-28T15:00:30Z",
              "actor": "ops.reviewer",
              "event": "decision.approved",
              "detail": {
                "authorized_arguments": {
                  "amount_usd": "18.00",
                  "order_id": "NW-17710",
                  "reason": "Cancelled before shipment; capture still open."
                },
                "proposed_arguments": {
                  "amount_usd": "18.00",
                  "order_id": "NW-17710",
                  "reason": "Cancelled before shipment; capture still open."
                },
                "reason": null
              },
              "gate_id": "gate_refund-expired"
            },
            {
              "id": 5,
              "ts": "2026-10-28T15:00:30Z",
              "actor": "agent",
              "event": "tool.executed",
              "detail": {
                "effect_id": "RF-5AD94AD2",
                "result": {
                  "amount_usd": "18.00",
                  "ok": true,
                  "order_id": "NW-17710",
                  "reason": "Cancelled before shipment; capture still open.",
                  "refund_id": "RF-5AD94AD2",
                  "status": "issued",
                  "tool": "issue_refund"
                }
              },
              "gate_id": "gate_refund-expired"
            },
            {
              "id": 6,
              "ts": "2026-10-28T15:00:30Z",
              "actor": "agent",
              "event": "run.completed",
              "detail": {
                "final_answer": "Issued refund RF-5AD94AD2 for $18.00 on order NW-17710."
              },
              "gate_id": "gate_refund-expired"
            }
          ]
        },
        "deny": {
          "actor": "ops.reviewer",
          "reason": "Let the cancel flow release the capture. Do not refund it here.",
          "edited_arguments": null,
          "preview": [
            {
              "label": "Order",
              "value": "NW-17710"
            },
            {
              "label": "Amount",
              "value": "$18.00"
            },
            {
              "label": "Captured",
              "value": "$18.00"
            },
            {
              "label": "Reason",
              "value": "Cancelled before shipment; capture still open."
            }
          ],
          "status": "denied",
          "final_answer": null,
          "result": null,
          "execution_count": 0,
          "idempotent_replays": 0,
          "steps": [
            {
              "kind": "human",
              "event": "decision.denied",
              "title": "Denied by ops.reviewer",
              "body": "Let the cancel flow release the capture. Do not refund it here.",
              "at": "2026-10-28T15:00:45Z"
            },
            {
              "kind": "stop",
              "event": "run.denied",
              "title": "Stopped",
              "body": "The tool was not called.",
              "at": "2026-10-28T15:00:45Z"
            }
          ],
          "audit": [
            {
              "id": 4,
              "ts": "2026-10-28T15:00:45Z",
              "actor": "ops.reviewer",
              "event": "decision.denied",
              "detail": {
                "reason": "Let the cancel flow release the capture. Do not refund it here."
              },
              "gate_id": "gate_refund-expired"
            },
            {
              "id": 5,
              "ts": "2026-10-28T15:00:45Z",
              "actor": "agent",
              "event": "run.denied",
              "detail": {
                "reason": "Let the cancel flow release the capture. Do not refund it here."
              },
              "gate_id": "gate_refund-expired"
            }
          ]
        },
        "edit": null,
        "late": {
          "actor": "ops.reviewer",
          "reason": null,
          "edited_arguments": null,
          "preview": [
            {
              "label": "Order",
              "value": "NW-17710"
            },
            {
              "label": "Amount",
              "value": "$18.00"
            },
            {
              "label": "Captured",
              "value": "$18.00"
            },
            {
              "label": "Reason",
              "value": "Cancelled before shipment; capture still open."
            }
          ],
          "status": "expired",
          "final_answer": null,
          "result": null,
          "execution_count": 0,
          "idempotent_replays": 0,
          "steps": [
            {
              "kind": "warn",
              "event": "gate.expired",
              "title": "Gate expired",
              "body": "expires_at 2026-10-28T16:00:00Z had passed. Nothing was executed.",
              "at": "2026-10-28T16:00:01Z"
            },
            {
              "kind": "stop",
              "event": "decision.rejected_expired",
              "title": "Late decision rejected",
              "body": "ops.reviewer sent approve after expiry.",
              "at": "2026-10-28T16:00:01Z"
            }
          ],
          "audit": [
            {
              "id": 4,
              "ts": "2026-10-28T16:00:01Z",
              "actor": "clock",
              "event": "gate.expired",
              "detail": {
                "expires_at": "2026-10-28T16:00:00Z"
              },
              "gate_id": "gate_refund-expired"
            },
            {
              "id": 5,
              "ts": "2026-10-28T16:00:01Z",
              "actor": "ops.reviewer",
              "event": "decision.rejected_expired",
              "detail": {
                "decision": "approve"
              },
              "gate_id": "gate_refund-expired"
            }
          ]
        }
      }
    }
  ]
};
