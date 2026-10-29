import json
import urllib.error
import urllib.request

import pytest

from agent_gate.api import create_app
from agent_gate.clock import ManualClock
from agent_gate.dataset import load_dataset
from agent_gate.engine import Engine
from agent_gate.errors import GateError
from agent_gate.llm import OllamaProvider, ReplayProvider
from agent_gate.models import DecisionIn, Message
from agent_gate.tools import ToolRegistry


def test_default_provider_is_mock(tmp_path, dataset_uri, monkeypatch):
    monkeypatch.delenv("HL_LLM_PROVIDER", raising=False)
    app = create_app(db_path=tmp_path / "gate.db", dataset_uri=dataset_uri)
    assert app.state.engine.llm.name == "mock"


def test_dataset_file_uri(tmp_path, dataset_uri):
    engine = Engine(
        db_path=tmp_path / "gate.db",
        dataset_uri="file://" + dataset_uri,
        llm_provider="mock",
        clock=ManualClock(),
    )
    view = engine.start("email-vendor")
    assert view.status == "awaiting_approval"


def test_replay_template_is_used(tmp_path, dataset_uri):
    dataset = load_dataset(dataset_uri)
    replays = dict(dataset.replays)
    replays["refund-stalled"] = replays["refund-stalled"].model_copy(
        update={"final_template": "REPLAY {refund_id}"}
    )
    engine = Engine(
        db_path=tmp_path / "gate.db",
        dataset=dataset,
        llm=ReplayProvider(replays),
        clock=ManualClock(),
    )
    view = engine.start("refund-stalled")
    result = engine.decide(
        DecisionIn(decision="approve", actor="ops.reviewer"),
        run_id=view.run_id,
    )
    assert result.run.final_answer.startswith("REPLAY RF-")


def test_ollama_parses_a_tool_call(monkeypatch, dataset_uri):
    captured = {}

    class Fake:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            body = {
                "message": {
                    "content": "draft",
                    "tool_calls": [
                        {
                            "function": {
                                "name": "issue_refund",
                                "arguments": {
                                    "order_id": "NW-18442",
                                    "amount_usd": "86.40",
                                    "reason": "Carrier never scanned the shipment.",
                                },
                            }
                        }
                    ],
                }
            }
            return json.dumps(body).encode()

    def urlopen(request, timeout=0):
        captured["url"] = request.full_url
        captured["body"] = json.loads(request.data.decode())
        return Fake()

    monkeypatch.setattr(urllib.request, "urlopen", urlopen)
    provider = OllamaProvider("http://127.0.0.1:11434", "qwen3:8b")
    tools = ToolRegistry(load_dataset(dataset_uri)).specs()
    turn = provider.complete([Message(role="user", content="Refund NW-18442.")], tools, None)
    assert captured["url"].endswith("/api/chat")
    assert captured["body"]["options"]["temperature"] == 0
    assert captured["body"]["options"]["seed"] == 42
    assert turn.tool_call is not None
    assert turn.tool_call.name == "issue_refund"
    assert any(tool["function"]["name"] == "issue_refund" for tool in captured["body"]["tools"])


def test_ollama_unreachable(monkeypatch):
    def urlopen(request, timeout=0):
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(urllib.request, "urlopen", urlopen)
    provider = OllamaProvider("http://127.0.0.1:11434", "qwen3:8b")
    with pytest.raises(GateError) as caught:
        provider.complete([], [], None)
    assert caught.value.status == 503
    assert "not reachable" in caught.value.message
