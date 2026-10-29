"""Errors that cross the engine / HTTP boundary."""

from __future__ import annotations

from typing import Any


class GateError(Exception):
    def __init__(
        self,
        status: int,
        code: str,
        message: str,
        *,
        run: dict[str, Any] | None = None,
        errors: list[dict[str, str]] | None = None,
        idempotent_replay: bool = False,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.run = run
        self.errors = errors
        self.idempotent_replay = idempotent_replay


class ArgError(Exception):
    """Tool arguments failed schema or policy checks."""

    def __init__(self, errors: list[dict[str, str]]) -> None:
        self.errors = errors
        super().__init__("; ".join(item["msg"] for item in errors))
