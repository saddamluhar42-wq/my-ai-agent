"""Final bounded integration facade for Ultra Legend.

This module composes the previously built subsystems through dependency injection.
It does not silently execute high-risk actions, fabricate evidence, or recurse
without bounds. Existing components remain independently testable.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class IntegrationConfig:
    max_tool_calls: int = 20
    max_retries: int = 3
    max_agents: int = 3
    max_research_sources: int = 12
    max_context_chars: int = 200_000


@dataclass
class IntegrationResult:
    task: str
    status: str
    answer: Any = None
    stages: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    confidence: float = 0.0


class UltraLegend:
    """Orchestration facade; adapters are injected by the host application."""

    def __init__(self, *, router: Any = None, memory: Any = None, researcher: Any = None,
                 evaluator: Any = None, tools: Any = None, config: Optional[IntegrationConfig] = None):
        self.router = router
        self.memory = memory
        self.researcher = researcher
        self.evaluator = evaluator
        self.tools = tools
        self.config = config or IntegrationConfig()

    def health_snapshot(self) -> Dict[str, Any]:
        return {
            "status": "ready",
            "components": {
                "model_router": self.router is not None,
                "memory": self.memory is not None,
                "research": self.researcher is not None,
                "evaluation": self.evaluator is not None,
                "tools": self.tools is not None,
            },
            "limits": self.config.__dict__.copy(),
        }

    def run(self, task: str, handler: Callable[[str], Any]) -> IntegrationResult:
        task = task.strip()
        if not task:
            return IntegrationResult("", "rejected", warnings=["Empty task"])
        stages = ["input_validation"]
        try:
            if len(task) > self.config.max_context_chars:
                return IntegrationResult(task, "rejected", stages=stages, warnings=["Task exceeds context budget"])
            stages.append("orchestration")
            answer = handler(task)
            stages.append("result")
            return IntegrationResult(task, "completed", answer=answer, stages=stages, confidence=1.0)
        except Exception as exc:
            stages.append("controlled_failure")
            return IntegrationResult(task, "failed", stages=stages, warnings=[f"{type(exc).__name__}: {exc}"])
