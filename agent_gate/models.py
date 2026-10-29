"""Pydantic models for runs, gates, and the public API."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

DecisionKind = Literal["approve", "deny", "edit"]
RunStatus = Literal[
    "running",
    "awaiting_approval",
    "executing",
    "completed",
    "denied",
    "expired",
    "failed",
]
ResumeCursor = Literal["draft", "execute_tool", "stopped"]


class ToolCall(BaseModel):
    id: str = ""
    name: str
    arguments: dict[str, Any]


class Message(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str
    tool_call: ToolCall | None = None
    tool_name: str | None = None


class AgentState(BaseModel):
    """The blob written to SQLite. A restarted process loads this and continues."""

    run_id: str
    scenario_id: str
    status: RunStatus
    messages: list[Message]
    pending_call: ToolCall | None = None
    gate_id: str | None = None
    resume_cursor: ResumeCursor
    tool_result: dict[str, Any] | None = None
    final_answer: str | None = None
    denial_reason: str | None = None
    error: list[dict[str, str]] | None = None
    created_at: str
    updated_at: str


class Draft(BaseModel):
    commentary: str
    tool: str
    arguments: dict[str, Any]


class EditExample(BaseModel):
    arguments: dict[str, Any]
    reason: str


class Scenario(BaseModel):
    id: str
    title: str
    summary: str
    lesson: str
    task: str
    risk_label: str
    draft: Draft
    deny_reason: str
    ttl_seconds: int | None = None
    edit_example: EditExample | None = None
    duplicate_approve: bool = False
    feature_expiry: bool = False


class ToolPolicy(BaseModel):
    requires_approval: bool
    ttl_seconds: int = Field(gt=0)
    description: str
    max_amount_usd: str | None = None


class Policy(BaseModel):
    tools: dict[str, ToolPolicy]


class ReplayTurn(BaseModel):
    commentary: str
    tool: str
    arguments: dict[str, Any]
    final_template: str | None = None


class DecisionIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision: DecisionKind
    actor: str = Field(default="ops.reviewer", min_length=1, max_length=80)
    reason: str | None = Field(default=None, max_length=500)
    edited_arguments: dict[str, Any] | None = None
    idempotency_key: str | None = Field(default=None, max_length=120)

    @model_validator(mode="after")
    def _check(self) -> DecisionIn:
        if self.decision == "edit" and not self.edited_arguments:
            raise ValueError("edit requires edited_arguments")
        if self.decision == "deny" and not (self.reason and self.reason.strip()):
            raise ValueError("deny requires a reason")
        if self.reason is not None:
            self.reason = self.reason.strip()
        return self


class CreateRun(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scenario_id: str = Field(min_length=1, max_length=80)


class AuditView(BaseModel):
    id: int
    ts: str
    actor: str
    event: str
    detail: dict[str, Any]
    gate_id: str | None = None


class GateView(BaseModel):
    gate_id: str
    tool_name: str
    arguments: dict[str, Any]
    proposed_arguments: dict[str, Any]
    status: str
    expires_at: str
    decision: dict[str, Any] | None = None
    execution: dict[str, Any] | None = None


class RunView(BaseModel):
    run_id: str
    scenario_id: str
    status: RunStatus
    created_at: str
    updated_at: str
    resume_cursor: ResumeCursor
    messages: list[Message]
    pending_call: ToolCall | None = None
    gate: GateView | None = None
    tool_result: dict[str, Any] | None = None
    final_answer: str | None = None
    denial_reason: str | None = None
    error: list[dict[str, str]] | None = None
    tool_execution_count: int = 0
    audit: list[AuditView] = Field(default_factory=list)


class RunSummary(BaseModel):
    run_id: str
    scenario_id: str
    status: str
    created_at: str
    updated_at: str
    tool_name: str | None = None
    gate_id: str | None = None
    expires_at: str | None = None


class DecisionResult(BaseModel):
    code: str
    idempotent_replay: bool = False
    run: RunView


class ScenarioSummary(BaseModel):
    id: str
    title: str
    summary: str
    lesson: str
    task: str
    risk_label: str
    tool: str
