"""Mock tools. They are pure functions of the fixture data plus the gate id.

A real refund API or DNS provider would be called with the gate id as its
idempotency key. Here the function only builds the ticket; the engine stores
that ticket once.
"""

from __future__ import annotations

import hashlib
import ipaddress
import json
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from agent_gate.dataset import Dataset
from agent_gate.errors import ArgError
from agent_gate.models import ToolPolicy

DOC_NET = ipaddress.ip_network("203.0.113.0/24")


class RefundArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    order_id: str = Field(pattern=r"^NW-\d{5}$")
    amount_usd: str = Field(pattern=r"^\d+\.\d{2}$")
    reason: str = Field(min_length=8, max_length=500)


class EmailArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    to: str = Field(min_length=3, max_length=200)
    subject: str = Field(min_length=3, max_length=120)
    body: str = Field(min_length=12, max_length=4000)


class DnsArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    zone: str
    name: str
    record_type: str = "A"
    value: str


SCHEMAS: dict[str, type[BaseModel]] = {
    "issue_refund": RefundArgs,
    "send_email": EmailArgs,
    "change_dns": DnsArgs,
}

TOOL_DESCRIPTIONS = {
    "issue_refund": "Refund a captured order, up to the captured total and the policy cap.",
    "send_email": "Queue an email to one address in the company directory.",
    "change_dns": "Change an existing A record inside an allowed zone. Values must be in 203.0.113.0/24.",
}


def usd_cents(value: str) -> int:
    whole, frac = value.split(".")
    if len(frac) != 2 or not whole.isdigit():
        raise ArgError([{"loc": "amount_usd", "msg": f"Not a dollar amount: {value}"}])
    return int(whole) * 100 + int(frac)


def effect_token(prefix: str, gate_id: str, tool: str, arguments: dict[str, Any]) -> str:
    blob = json.dumps(
        {"args": arguments, "gate_id": gate_id, "tool": tool},
        sort_keys=True,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(blob.encode()).hexdigest()[:8].upper()
    return f"{prefix}{digest}"


def summarize_result(result: dict[str, Any]) -> str:
    tool = result.get("tool")
    if tool == "issue_refund":
        return (
            f"Issued refund {result['refund_id']} for ${result['amount_usd']} "
            f"on order {result['order_id']}."
        )
    if tool == "send_email":
        return f"Queued {result['message_id']} to {result['to']}."
    if tool == "change_dns":
        return (
            f"Updated {result['name']} from {result['previous']} "
            f"to {result['value']} ({result['change_id']})."
        )
    return f"{tool} finished."


def _pydantic_errors(exc: ValidationError) -> list[dict[str, str]]:
    errors = []
    for item in exc.errors():
        loc = ".".join(str(part) for part in item["loc"])
        errors.append({"loc": loc or "arguments", "msg": item["msg"]})
    return errors


class ToolRegistry:
    def __init__(self, dataset: Dataset) -> None:
        self.dataset = dataset

    def specs(self) -> list[dict[str, Any]]:
        specs = []
        for name, model in SCHEMAS.items():
            policy = self.dataset.policy.tools.get(name)
            description = policy.description if policy else TOOL_DESCRIPTIONS[name]
            specs.append(
                {
                    "name": name,
                    "description": description,
                    "parameters": model.model_json_schema(),
                }
            )
        return specs

    def policy_for(self, name: str) -> ToolPolicy:
        try:
            return self.dataset.policy.tools[name]
        except KeyError as exc:
            raise ArgError([{"loc": "tool", "msg": f"Unknown tool {name!r}."}]) from exc

    def validate(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        model = SCHEMAS.get(name)
        if model is None:
            raise ArgError([{"loc": "tool", "msg": f"Unknown tool {name!r}."}])
        try:
            parsed = model.model_validate(arguments)
        except ValidationError as exc:
            raise ArgError(_pydantic_errors(exc)) from exc
        data = parsed.model_dump()
        self._policy(name, data)
        return data

    def _policy(self, name: str, arguments: dict[str, Any]) -> None:
        if name == "issue_refund":
            self._refund_policy(arguments)
        elif name == "send_email":
            self._email_policy(arguments)
        elif name == "change_dns":
            self._dns_policy(arguments)

    def _refund_policy(self, arguments: dict[str, Any]) -> None:
        order = self.dataset.orders.get(arguments["order_id"])
        if order is None:
            raise ArgError(
                [{"loc": "order_id", "msg": f"No order {arguments['order_id']} in the fixture."}]
            )
        if order["status"] == "disputed_locked":
            raise ArgError(
                [{"loc": "order_id", "msg": f"{arguments['order_id']} is locked by a dispute."}]
            )
        amount = usd_cents(arguments["amount_usd"])
        if amount <= 0:
            raise ArgError([{"loc": "amount_usd", "msg": "Amount must be greater than zero."}])
        captured = usd_cents(order["total_usd"])
        if amount > captured:
            raise ArgError(
                [
                    {
                        "loc": "amount_usd",
                        "msg": (
                            f"Amount {arguments['amount_usd']} exceeds the captured "
                            f"total of {order['total_usd']}."
                        ),
                    }
                ]
            )
        policy = self.policy_for("issue_refund")
        if policy.max_amount_usd is not None and amount > usd_cents(policy.max_amount_usd):
            raise ArgError(
                [
                    {
                        "loc": "amount_usd",
                        "msg": f"Amount exceeds the policy cap of {policy.max_amount_usd}.",
                    }
                ]
            )

    def _email_policy(self, arguments: dict[str, Any]) -> None:
        address = arguments["to"].strip()
        if address.casefold() not in self.dataset.directory:
            raise ArgError(
                [
                    {
                        "loc": "to",
                        "msg": f"{address} is not in the directory. Refusing to invent a recipient.",
                    }
                ]
            )
        arguments["to"] = self.dataset.directory[address.casefold()]["address"]

    def _dns_policy(self, arguments: dict[str, Any]) -> None:
        if arguments["record_type"] != "A":
            raise ArgError([{"loc": "record_type", "msg": "Only A records can be changed here."}])
        zone = self.dataset.zones.get(arguments["zone"])
        if zone is None:
            raise ArgError([{"loc": "zone", "msg": f"Zone {arguments['zone']} is not allowed."}])
        current = next((row for row in zone["records"] if row["name"] == arguments["name"]), None)
        if current is None:
            raise ArgError(
                [{"loc": "name", "msg": f"{arguments['name']} is not an existing record in the zone."}]
            )
        if not arguments["name"].endswith(arguments["zone"]):
            raise ArgError([{"loc": "name", "msg": "Record name must sit inside the zone."}])
        try:
            ip = ipaddress.ip_address(arguments["value"])
        except ValueError as exc:
            raise ArgError([{"loc": "value", "msg": "Value is not an IP address."}]) from exc
        if ip not in DOC_NET:
            raise ArgError(
                [
                    {
                        "loc": "value",
                        "msg": "New A records must use the documentation range 203.0.113.0/24.",
                    }
                ]
            )
        if arguments["value"] == current["value"]:
            raise ArgError(
                [{"loc": "value", "msg": f"{arguments['name']} is already {current['value']}."}]
            )

    def perform(self, name: str, arguments: dict[str, Any], *, gate_id: str) -> dict[str, Any]:
        authorized = self.validate(name, arguments)
        if name == "issue_refund":
            token = effect_token("RF-", gate_id, name, authorized)
            return {
                "ok": True,
                "tool": name,
                "refund_id": token,
                "order_id": authorized["order_id"],
                "amount_usd": authorized["amount_usd"],
                "reason": authorized["reason"],
                "status": "issued",
            }
        if name == "send_email":
            token = effect_token("MSG-", gate_id, name, authorized)
            return {
                "ok": True,
                "tool": name,
                "message_id": token,
                "to": authorized["to"],
                "subject": authorized["subject"],
                "status": "queued",
            }
        if name == "change_dns":
            zone = self.dataset.zones[authorized["zone"]]
            current = next(row for row in zone["records"] if row["name"] == authorized["name"])
            token = effect_token("DNS-", gate_id, name, authorized)
            return {
                "ok": True,
                "tool": name,
                "change_id": token,
                "zone": authorized["zone"],
                "name": authorized["name"],
                "record_type": "A",
                "previous": current["value"],
                "value": authorized["value"],
                "status": "applied",
            }
        raise ArgError([{"loc": "tool", "msg": f"Unknown tool {name!r}."}])

    def preview(self, name: str, arguments: dict[str, Any]) -> list[dict[str, str]]:
        """Rows for the approval card. Read-only."""
        if name == "issue_refund":
            order = self.dataset.orders.get(arguments.get("order_id", ""), {})
            return [
                {"label": "Order", "value": str(arguments.get("order_id", ""))},
                {"label": "Amount", "value": f"${arguments.get('amount_usd', '')}"},
                {"label": "Captured", "value": f"${order.get('total_usd', '—')}"},
                {"label": "Reason", "value": str(arguments.get("reason", ""))},
            ]
        if name == "send_email":
            return [
                {"label": "To", "value": str(arguments.get("to", ""))},
                {"label": "Subject", "value": str(arguments.get("subject", ""))},
                {"label": "Body", "value": str(arguments.get("body", ""))},
            ]
        if name == "change_dns":
            zone = self.dataset.zones.get(arguments.get("zone", ""))
            current = "—"
            if zone:
                row = next(
                    (item for item in zone["records"] if item["name"] == arguments.get("name")),
                    None,
                )
                if row:
                    current = row["value"]
            return [
                {"label": "Record", "value": str(arguments.get("name", ""))},
                {"label": "Type", "value": str(arguments.get("record_type", "A"))},
                {"label": "From", "value": current},
                {"label": "To", "value": str(arguments.get("value", ""))},
            ]
        return [{"label": "Arguments", "value": json.dumps(arguments, sort_keys=True)}]
