"""Continuous evaluation and benchmark primitives for the agent.

Keeps evaluation deterministic and auditable. Scores are signals, not proof of
correctness, and benchmark data is never executed as instructions.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Iterable, List, Optional
import json
import os


@dataclass
class EvalCase:
    case_id: str
    task: str
    expected: Any = None
    tags: List[str] = field(default_factory=list)
    validator: Optional[Callable[[Any, Any], bool]] = None


@dataclass
class EvalResult:
    case_id: str
    passed: bool
    score: float
    output: Any = None
    error: Optional[str] = None
    notes: List[str] = field(default_factory=list)


@dataclass
class BenchmarkReport:
    run_id: str
    total: int
    passed: int
    failed: int
    pass_rate: float
    average_score: float
    results: List[EvalResult]
    created_at: str


class ContinuousEvaluator:
    """Run bounded regression benchmarks against an injected agent callable."""

    def __init__(self, max_cases: int = 100):
        self.max_cases = max(1, min(1000, max_cases))

    @staticmethod
    def _default_validate(output: Any, expected: Any) -> bool:
        return output == expected

    def run(self, agent: Callable[[str], Any], cases: Iterable[EvalCase], run_id: str = "benchmark") -> BenchmarkReport:
        results: List[EvalResult] = []
        for case in list(cases)[: self.max_cases]:
            try:
                output = agent(case.task)
                validator = case.validator or self._default_validate
                passed = bool(validator(output, case.expected))
                results.append(EvalResult(case.case_id, passed, 1.0 if passed else 0.0, output=output))
            except Exception as exc:
                results.append(EvalResult(case.case_id, False, 0.0, error=str(exc)))
        total = len(results)
        passed = sum(r.passed for r in results)
        average = sum(r.score for r in results) / total if total else 0.0
        return BenchmarkReport(
            run_id=run_id,
            total=total,
            passed=passed,
            failed=total - passed,
            pass_rate=passed / total if total else 0.0,
            average_score=average,
            results=results,
            created_at=datetime.now(timezone.utc).isoformat(),
        )


class RegressionGate:
    """Prevent a candidate from being considered better when it regresses."""

    def __init__(self, minimum_pass_rate: float = 0.80, allowed_drop: float = 0.02):
        self.minimum_pass_rate = max(0.0, min(1.0, minimum_pass_rate))
        self.allowed_drop = max(0.0, min(1.0, allowed_drop))

    def approve(self, candidate: BenchmarkReport, baseline: Optional[BenchmarkReport] = None) -> Dict[str, Any]:
        reasons: List[str] = []
        if candidate.pass_rate < self.minimum_pass_rate:
            reasons.append("Candidate is below minimum pass-rate threshold")
        if baseline is not None and candidate.pass_rate < baseline.pass_rate - self.allowed_drop:
            reasons.append("Candidate regresses beyond allowed baseline drop")
        return {"approved": not reasons, "reasons": reasons, "candidate_pass_rate": candidate.pass_rate,
                "baseline_pass_rate": baseline.pass_rate if baseline else None}


class BenchmarkStore:
    """Append-only JSONL report store for auditable evaluation history."""

    def __init__(self, path: str = "data/evaluation_history.jsonl"):
        self.path = path
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

    def append(self, report: BenchmarkReport) -> None:
        with open(self.path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(report), ensure_ascii=False, default=str) + "\n")
