"""Skill/tool discovery and bounded plugin orchestration."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Optional


@dataclass
class ToolSpec:
    name: str
    description: str
    capabilities: List[str] = field(default_factory=list)
    risk: str = "low"
    enabled: bool = True


@dataclass
class ToolSelection:
    tool: str
    score: float
    reasons: List[str]


class ToolRegistry:
    def __init__(self):
        self._specs: Dict[str, ToolSpec] = {}
        self._handlers: Dict[str, Callable[..., Any]] = {}

    def register(self, spec: ToolSpec, handler: Optional[Callable[..., Any]] = None) -> None:
        self._specs[spec.name] = spec
        if handler:
            self._handlers[spec.name] = handler

    def discover(self, task: str, required_capabilities: Optional[Iterable[str]] = None, limit: int = 5) -> List[ToolSelection]:
        terms = {x.lower() for x in task.split() if len(x) > 2}
        required = {x.lower() for x in (required_capabilities or [])}
        results: List[ToolSelection] = []
        for spec in self._specs.values():
            if not spec.enabled:
                continue
            caps = {x.lower() for x in spec.capabilities}
            overlap = len(terms & caps) / max(1, len(terms))
            required_hit = len(required & caps) / max(1, len(required))
            risk_penalty = {"low": 0.0, "medium": 0.10, "high": 0.25}.get(spec.risk.lower(), 0.25)
            score = max(0.0, min(1.0, 0.65 * required_hit + 0.35 * overlap - risk_penalty))
            results.append(ToolSelection(spec.name, round(score, 4), [f"capability_match={required_hit:.2f}", f"task_match={overlap:.2f}", f"risk={spec.risk}"]))
        return sorted(results, key=lambda x: x.score, reverse=True)[: max(1, limit)]

    def execute(self, selection: ToolSelection, args: Optional[Dict[str, Any]] = None, *, allow_actions: bool = False) -> Any:
        spec = self._specs.get(selection.tool)
        if not spec or not spec.enabled:
            raise RuntimeError("Tool is unavailable or disabled")
        if spec.risk.lower() != "low" and not allow_actions:
            raise PermissionError("Explicit action approval required")
        handler = self._handlers.get(selection.tool)
        if not handler:
            return {"status": "discovered", "tool": selection.tool, "description": spec.description}
        return handler(**(args or {}))


class PluginOrchestrator:
    """Plan tool chains without recursive/unbounded plugin spawning."""

    def __init__(self, registry: ToolRegistry, max_tools: int = 4):
        self.registry = registry
        self.max_tools = max(1, min(8, max_tools))

    def plan(self, task: str, required_capabilities: Optional[List[str]] = None) -> List[ToolSelection]:
        return self.registry.discover(task, required_capabilities, self.max_tools)

    def run(self, task: str, required_capabilities: Optional[List[str]] = None, *, allow_actions: bool = False) -> List[Dict[str, Any]]:
        results = []
        for selection in self.plan(task, required_capabilities):
            try:
                output = self.registry.execute(selection, allow_actions=allow_actions)
                results.append({"tool": selection.tool, "score": selection.score, "result": output})
            except Exception as exc:
                results.append({"tool": selection.tool, "score": selection.score, "error": str(exc)})
        return results
