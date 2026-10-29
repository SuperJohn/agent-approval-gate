import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agent_gate.api import create_app  # noqa: E402
from agent_gate.clock import ManualClock  # noqa: E402
from agent_gate.engine import Engine  # noqa: E402

DATA = ROOT / "demo" / "data"


@pytest.fixture
def dataset_uri() -> str:
    return str(DATA)


@pytest.fixture
def clock() -> ManualClock:
    return ManualClock()


@pytest.fixture
def engine(tmp_path: Path, dataset_uri: str, clock: ManualClock) -> Engine:
    return Engine(
        db_path=tmp_path / "gate.db",
        dataset_uri=dataset_uri,
        llm_provider="mock",
        clock=clock,
    )


@pytest.fixture
def client(tmp_path: Path, dataset_uri: str, clock: ManualClock):
    app = create_app(
        db_path=tmp_path / "gate.db",
        dataset_uri=dataset_uri,
        llm_provider="mock",
        clock=clock,
    )
    with TestClient(app) as test_client:
        yield test_client
