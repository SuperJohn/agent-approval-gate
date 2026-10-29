"""`python -m agent_gate` serves the local API."""

from __future__ import annotations

import os

import uvicorn


def main() -> None:
    port = int(os.environ.get("PORT", "8787"))
    uvicorn.run(
        "agent_gate.api:create_app",
        factory=True,
        host="127.0.0.1",
        port=port,
    )


if __name__ == "__main__":
    main()
