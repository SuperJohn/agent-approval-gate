"""Load the synthetic dataset pointed at by HL_DATASET_URI."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlparse

from agent_gate.errors import GateError
from agent_gate.models import Policy, ReplayTurn, Scenario

DEFAULT_URI = "demo/data"


def resolve_dataset_uri(uri: str | None) -> Path:
    raw = uri or os.environ.get("HL_DATASET_URI") or DEFAULT_URI
    if raw.startswith("file://"):
        parsed = urlparse(raw)
        return Path(unquote(parsed.path))
    return Path(raw)


def _load(path: Path) -> object:
    if not path.is_file():
        raise GateError(500, "dataset", f"Missing dataset file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


@dataclass
class Dataset:
    root: Path
    scenarios: dict[str, Scenario]
    orders: dict[str, dict]
    zones: dict[str, dict]
    directory: dict[str, dict]
    policy: Policy
    replays: dict[str, ReplayTurn]

    def scenario(self, scenario_id: str) -> Scenario:
        try:
            return self.scenarios[scenario_id]
        except KeyError as exc:
            known = ", ".join(sorted(self.scenarios))
            raise GateError(
                404,
                "unknown_scenario",
                f"Unknown scenario {scenario_id!r}. Known: {known}.",
            ) from exc


def load_dataset(uri: str | None = None) -> Dataset:
    root = resolve_dataset_uri(uri)
    if not root.is_dir():
        raise GateError(500, "dataset", f"Dataset directory does not exist: {root}")

    raw_scenarios = _load(root / "scenarios.json")
    if not isinstance(raw_scenarios, list):
        raise GateError(500, "dataset", "scenarios.json must be a list")
    scenarios = {}
    for item in raw_scenarios:
        scenario = Scenario.model_validate(item)
        if scenario.id in scenarios:
            raise GateError(500, "dataset", f"Duplicate scenario id {scenario.id}")
        scenarios[scenario.id] = scenario

    orders_raw = _load(root / "orders.json")
    zones_raw = _load(root / "zones.json")
    directory_raw = _load(root / "directory.json")
    policy = Policy.model_validate(_load(root / "policy.json"))
    replays_raw = _load(root / "replays.json")

    if not isinstance(orders_raw, list):
        raise GateError(500, "dataset", "orders.json must be a list")
    orders = {row["order_id"]: row for row in orders_raw}

    if not isinstance(zones_raw, dict) or not isinstance(zones_raw.get("zones"), list):
        raise GateError(500, "dataset", "zones.json must contain a zones list")
    zones = {zone["zone"]: zone for zone in zones_raw["zones"]}

    if not isinstance(directory_raw, dict):
        raise GateError(500, "dataset", "directory.json must be an object")
    mailboxes = directory_raw.get("mailboxes")
    if not isinstance(mailboxes, list):
        raise GateError(500, "dataset", "directory.json must contain mailboxes")
    directory = {row["address"].casefold(): row for row in mailboxes}

    if not isinstance(replays_raw, dict):
        raise GateError(500, "dataset", "replays.json must be an object")
    replays = {key: ReplayTurn.model_validate(value) for key, value in replays_raw.items()}

    return Dataset(
        root=root,
        scenarios=scenarios,
        orders=orders,
        zones=zones,
        directory=directory,
        policy=policy,
        replays=replays,
    )
