"""External Coder plugin adapter.

The agent never executes generated code locally. The configured HTTPS endpoint
must belong to a separately hosted sandbox/coder service.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from plugins.manager import execute_plugin


@dataclass(frozen=True)
class CoderPlugin:
    name: str = "Coder"
    version: str = "1.1.0"
    capabilities: tuple[str, ...] = (
        "code_generation",
        "code_review",
        "debugging",
        "repository_tasks",
    )
    execution: str = "external_https_sandbox"

    @property
    def endpoint(self) -> str:
        return os.getenv("CODER_PLUGIN_ENDPOINT", "").strip()

    @property
    def connected(self) -> bool:
        return bool(self.endpoint)

    def run(self, capability: str, prompt: str, context: dict | None = None) -> dict:
        if capability not in self.capabilities:
            raise ValueError(f"Unsupported Coder capability: {capability}")
        if not self.endpoint:
            raise RuntimeError("CODER_PLUGIN_ENDPOINT is not configured in the server environment.")
        return execute_plugin(
            self.endpoint,
            capability,
            {"prompt": str(prompt or "").strip(), "context": context or {}},
        )


plugin = CoderPlugin()
