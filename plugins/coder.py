"""Lightweight coder-plugin descriptor used by the Plugin Manager.

This module intentionally contains metadata only. Actual code execution must
be delegated to a separately connected HTTPS sandbox/plugin service.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CoderPlugin:
    name: str = "Coder"
    version: str = "1.0.0"
    capabilities: tuple[str, ...] = (
        "code_generation",
        "code_review",
        "debugging",
        "repository_tasks",
    )
    execution: str = "external_sandbox_required"


plugin = CoderPlugin()
