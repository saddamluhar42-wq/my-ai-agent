"""Production hardening, health checks, limits, and structured observability."""
from __future__ import annotations

import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional


@dataclass
class RuntimeLimits:
    max_tool_calls: int = 20
    max_retries: int = 3
    max_research_sources: int = 50
    max_context_chars: int = 200_000
    timeout_seconds: float = 120.0


@dataclass
class HealthStatus:
    healthy: bool
    checks: Dict[str, bool] = field(default_factory=dict)
    details: Dict[str, str] = field(default_factory=dict)


class OperationBudget:
    """Per-operation budget preventing runaway tool/retry usage."""

    def __init__(self, limits: Optional[RuntimeLimits] = None):
        self.limits = limits or RuntimeLimits()
        self.tool_calls = 0
        self.retries = 0
        self.started = time.monotonic()

    def check_timeout(self) -> None:
        if time.monotonic() - self.started > self.limits.timeout_seconds:
            raise TimeoutError("Operation exceeded runtime budget")

    def consume_tool(self) -> None:
        self.check_timeout()
        self.tool_calls += 1
        if self.tool_calls > self.limits.max_tool_calls:
            raise RuntimeError("Tool-call budget exceeded")

    def consume_retry(self) -> None:
        self.check_timeout()
        self.retries += 1
        if self.retries > self.limits.max_retries:
            raise RuntimeError("Retry budget exceeded")


class StructuredLogger:
    """Small JSON-compatible event logger with request correlation."""

    def __init__(self, name: str = "ultra_legend"):
        self.logger = logging.getLogger(name)

    def event(self, event: str, *, request_id: Optional[str] = None, **fields: Any) -> Dict[str, Any]:
        payload = {"event": event, "request_id": request_id or str(uuid.uuid4()), **fields}
        self.logger.info("%s", payload)
        return payload


class ProductionHealth:
    def __init__(self, memory_path: str = "data/long_term_memory.sqlite3"):
        self.memory_path = memory_path

    def check(self, *, required_env: tuple[str, ...] = ()) -> HealthStatus:
        checks: Dict[str, bool] = {
            "python_runtime": True,
            "memory_directory": os.path.isdir(os.path.dirname(self.memory_path) or "."),
        }
        details: Dict[str, str] = {}
        for key in required_env:
            ok = bool(os.getenv(key))
            checks[f"env:{key}"] = ok
            if not ok:
                details[f"env:{key}"] = "Required environment variable is missing"
        return HealthStatus(all(checks.values()), checks, details)


def guarded_call(operation: Callable[[], Any], budget: OperationBudget, logger: Optional[StructuredLogger] = None) -> Any:
    request_id = str(uuid.uuid4())
    try:
        budget.check_timeout()
        result = operation()
        if logger:
            logger.event("operation_completed", request_id=request_id)
        return result
    except Exception as exc:
        if logger:
            logger.event("operation_failed", request_id=request_id, error_type=type(exc).__name__)
        raise
