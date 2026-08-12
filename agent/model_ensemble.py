"""Advanced model routing and ensemble primitives.

Routes by task requirements and combines independent candidate outputs without
pretending that agreement is proof. External model calls are injected as adapters.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class ModelProfile:
    name: str
    strengths: List[str] = field(default_factory=list)
    cost: float = 0.5
    latency: float = 0.5
    reliability: float = 0.8
    context_limit: int = 100000


@dataclass
class RouteDecision:
    selected: List[str]
    scores: Dict[str, float]
    reason: str


@dataclass
class EnsembleResult:
    candidates: Dict[str, Any]
    selected: Any
    agreement: float
    confidence: float
    notes: List[str] = field(default_factory=list)


class ModelEnsemble:
    """Capability-aware router with bounded parallel candidates."""

    def __init__(self, profiles: Optional[List[ModelProfile]] = None, max_models: int = 3):
        self.profiles = profiles or []
        self.max_models = max(1, min(5, max_models))

    def route(self, task: str, requirements: Optional[List[str]] = None) -> RouteDecision:
        req = {x.lower() for x in (requirements or [])}
        text = task.lower()
        scores: Dict[str, float] = {}
        for model in self.profiles:
            capability = sum(1 for s in model.strengths if s.lower() in req or s.lower() in text)
            score = 0.50 * model.reliability + 0.25 * (capability / max(1, len(req))) + 0.15 * (1 - model.latency) + 0.10 * (1 - model.cost)
            scores[model.name] = round(score, 4)
        selected = sorted(scores, key=scores.get, reverse=True)[: self.max_models]
        return RouteDecision(selected, scores, "Selected by capability, reliability, latency and cost.")

    def run(self, task: str, adapters: Dict[str, Callable[[str], Any]], requirements: Optional[List[str]] = None) -> EnsembleResult:
        decision = self.route(task, requirements)
        candidates: Dict[str, Any] = {}
        for name in decision.selected:
            adapter = adapters.get(name)
            if adapter is None:
                continue
            try:
                candidates[name] = adapter(task)
            except Exception as exc:
                candidates[name] = {"error": str(exc)}
        valid = [v for v in candidates.values() if not isinstance(v, dict) or "error" not in v]
        if not valid:
            return EnsembleResult(candidates, None, 0.0, 0.0, ["No model produced a usable result."])
        normalized = [str(v).strip() for v in valid]
        agreement = 1.0 if len(set(normalized)) == 1 else 0.5 if len(normalized) > 1 else 0.0
        confidence = min(1.0, agreement * (0.5 + 0.5 * len(valid) / max(1, len(decision.selected))))
        notes = ["Model agreement is a consistency signal, not proof of correctness."]
        if len(set(normalized)) > 1:
            notes.append("Candidates disagree; downstream verification is recommended.")
        return EnsembleResult(candidates, valid[0], agreement, confidence, notes)
