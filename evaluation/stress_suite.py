"""Bounded stress and integration checks for Ultra Legend components."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List


@dataclass
class StressCase:
    name: str
    operation: Callable[[], Any]


@dataclass
class StressResult:
    name: str
    passed: bool
    error: str = ""


class StressSuite:
    def __init__(self, max_cases: int = 50):
        self.max_cases = max(1, min(200, max_cases))

    def run(self, cases: Iterable[StressCase]) -> List[StressResult]:
        results: List[StressResult] = []
        for case in list(cases)[: self.max_cases]:
            try:
                case.operation()
                results.append(StressResult(case.name, True))
            except Exception as exc:
                results.append(StressResult(case.name, False, f"{type(exc).__name__}: {exc}"))
        return results

    @staticmethod
    def summary(results: List[StressResult]) -> Dict[str, Any]:
        total = len(results)
        passed = sum(r.passed for r in results)
        return {
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": passed / total if total else 0.0,
            "failures": [{"name": r.name, "error": r.error} for r in results if not r.passed],
        }
