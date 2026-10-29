"""Injectable clocks. Tests and the site recording never read the wall clock."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        raise ValueError("naive datetimes are not allowed")
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError(f"timestamp {value!r} has no timezone")
    return parsed.astimezone(timezone.utc)


class SystemClock:
    def now(self) -> datetime:
        return utcnow()


class ManualClock:
    """A clock that moves only when a test or the recorder says so."""

    def __init__(self, start: datetime | None = None) -> None:
        self.current = start or datetime(2026, 10, 28, 15, 0, 0, tzinfo=timezone.utc)

    def now(self) -> datetime:
        return self.current

    def advance(self, seconds: int) -> None:
        self.current = self.current + timedelta(seconds=seconds)
