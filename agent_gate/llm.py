"""Pluggable model providers.

`mock` (the default) and `replay` are deterministic and need no keys.
`ollama` calls a local server when HL_LLM_PROVIDER=ollama.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Protocol

from pydantic import BaseModel

from agent_gate.dataset import Dataset
from agent_gate.errors import GateError
from agent_gate.models import Message, ReplayTurn, Scenario, ToolCall
from agent_gate.tools import summarize_result

SYSTEM_PROMPT = (
    "You are the operations agent for Northwind Field Goods, a fictional mail-order "
    "company used as a demo. Act only through the provided tools. Use only ids, amounts, "
    "and addresses that appear in the task or the tool results. Do not invent personal data. "
    "When a tool is high-stakes, still propose exactly one tool call; a human gate will pause "
    "it. After a tool result, reply with one short factual sentence and do not call another tool."
)


class Turn(BaseModel):
    content: str
    tool_call: ToolCall | None = None


class LLM(Protocol):
    name: str

    def complete(
        self,
        messages: list[Message],
        tools: list[dict],
        scenario: Scenario | None,
    ) -> Turn: ...


def _last_tool_result(messages: list[Message]) -> dict | None:
    for message in reversed(messages):
        if message.role == "tool":
            return json.loads(message.content)
    return None


class MockProvider:
    """Follow the scenario script. The final sentence is derived from the tool result."""

    name = "mock"

    def complete(
        self,
        messages: list[Message],
        tools: list[dict],
        scenario: Scenario | None,
    ) -> Turn:
        del tools
        result = _last_tool_result(messages)
        if result is not None:
            return Turn(content=summarize_result(result))
        if scenario is None:
            raise GateError(
                400,
                "mock",
                "The mock provider only runs scenarios from the dataset.",
            )
        return Turn(
            content=scenario.draft.commentary,
            tool_call=ToolCall(
                name=scenario.draft.tool,
                arguments=dict(scenario.draft.arguments),
            ),
        )


class ReplayProvider:
    """Serve a saved transcript from demo/data/replays.json."""

    name = "replay"

    def __init__(self, replays: dict[str, ReplayTurn]) -> None:
        self.replays = replays

    def complete(
        self,
        messages: list[Message],
        tools: list[dict],
        scenario: Scenario | None,
    ) -> Turn:
        del tools
        if scenario is None or scenario.id not in self.replays:
            raise GateError(500, "replay", "No replay transcript for this scenario.")
        saved = self.replays[scenario.id]
        result = _last_tool_result(messages)
        if result is not None:
            if saved.final_template:
                try:
                    text = saved.final_template.format(**result)
                except KeyError as exc:
                    raise GateError(
                        500,
                        "replay",
                        f"Replay template is missing {{{exc.args[0]}}}.",
                    ) from exc
                return Turn(content=text)
            return Turn(content=summarize_result(result))
        return Turn(
            content=saved.commentary,
            tool_call=ToolCall(name=saved.tool, arguments=dict(saved.arguments)),
        )


class OllamaProvider:
    """Optional local model. Not used in CI."""

    name = "ollama"

    def __init__(self, base_url: str, model: str, timeout: float = 60) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def complete(
        self,
        messages: list[Message],
        tools: list[dict],
        scenario: Scenario | None,
    ) -> Turn:
        del scenario
        body = {
            "model": self.model,
            "stream": False,
            "messages": [_ollama_message(message) for message in messages],
            "tools": [_ollama_tool(tool) for tool in tools],
            "options": {"temperature": 0, "seed": 42},
        }
        request = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode())
        except urllib.error.URLError as exc:
            raise GateError(
                503,
                "ollama_unreachable",
                f"Ollama is not reachable at {self.base_url} ({exc.reason}).",
            ) from exc
        message = payload.get("message") or {}
        calls = message.get("tool_calls") or []
        content = message.get("content") or ""
        if not calls:
            return Turn(content=content)
        function = calls[0].get("function") or {}
        arguments = function.get("arguments") or {}
        if isinstance(arguments, str):
            arguments = json.loads(arguments) if arguments else {}
        if not isinstance(arguments, dict):
            raise GateError(502, "ollama_bad_response", "Tool arguments were not an object.")
        return Turn(
            content=content,
            tool_call=ToolCall(name=function.get("name") or "", arguments=arguments),
        )


def _ollama_message(message: Message) -> dict:
    if message.role == "assistant" and message.tool_call is not None:
        return {
            "role": "assistant",
            "content": message.content,
            "tool_calls": [
                {
                    "type": "function",
                    "function": {
                        "name": message.tool_call.name,
                        "arguments": message.tool_call.arguments,
                    },
                }
            ],
        }
    if message.role == "tool":
        return {"role": "tool", "name": message.tool_name or "", "content": message.content}
    return {"role": message.role, "content": message.content}


def _ollama_tool(spec: dict) -> dict:
    return {
        "type": "function",
        "function": {
            "name": spec["name"],
            "description": spec["description"],
            "parameters": spec["parameters"],
        },
    }


def build_llm(name: str | None, dataset: Dataset) -> LLM:
    key = (name if name is not None else os.environ.get("HL_LLM_PROVIDER") or "mock").lower()
    if key == "mock":
        return MockProvider()
    if key == "replay":
        return ReplayProvider(dataset.replays)
    if key == "ollama":
        timeout = float(os.environ.get("HL_OLLAMA_TIMEOUT", "60"))
        return OllamaProvider(
            base_url=os.environ.get("HL_OLLAMA_URL", "http://127.0.0.1:11434"),
            model=os.environ.get("HL_OLLAMA_MODEL", "qwen3:8b"),
            timeout=timeout,
        )
    raise GateError(
        500,
        "config",
        f"Unknown HL_LLM_PROVIDER {key!r}. Use mock, replay, or ollama.",
    )
