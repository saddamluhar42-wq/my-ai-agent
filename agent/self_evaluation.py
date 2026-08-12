"""Self-evaluation, bounded recovery, and task-memory primitives."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class EvaluationStatus(str, Enum):
    PASS = "pass"
    RETRY = "retry"
    FAIL = "fail"


@dataclass
class Evaluation:
    status: EvaluationStatus
    score: float
    reasons: List[str] = field(default_factory=list)
    corrections: List[str] = field(default_factory=list)


@dataclass
class TaskMemory:
    task: str
    attempts: int = 0
    successful_steps: List[str] = field(default_factory=list)
    failed_steps: List[str] = field(default_factory=list)
    lessons: List[str] = field(default_factory=list)
    final_result: Any = None


class SelfEvaluator:
    """Deterministic guardrail layer; model critique can be supplied separately."""

    def evaluate(self, result: Any, *, expected: Optional[Callable[[Any], bool]] = None) -> Evaluation:
        reasons: List[str] = []
        if result is None:
            return Evaluation(EvaluationStatus.RETRY, 0.0, ["Empty result"], ["Retry with missing output diagnostics"])
        if expected is not None:
            try:
                if not expected(result):
                    return Evaluation(EvaluationStatus.RETRY, 0.4, ["Output failed expected-condition check"], ["Revise output and retry"])
            except Exception as exc:
                reasons.append(f"Validator error: {exc}")
        return Evaluation(EvaluationStatus.PASS, 1.0, reasons)


class RecoveryController:
    """Bounded retry controller; never retries indefinitely."""

    def __init__(self, max_retries: int = 2):
        self.max_retries = max(0, max_retries)

    def run(self, operation: Callable[[], Any], evaluator: SelfEvaluator, *, expected: Optional[Callable[[Any], bool]] = None) -> tuple[Any, Evaluation, int]:
        last_result: Any = None
        last_eval = Evaluation(EvaluationStatus.FAIL, 0.0, ["No attempt made"])
        for attempt in range(self.max_retries + 1):
            last_result = operation()
            last_eval = evaluator.evaluate(last_result, expected=expected)
            if last_eval.status == EvaluationStatus.PASS:
                return last_result, last_eval, attempt + 1
        return last_result, Evaluation(EvaluationStatus.FAIL, last_eval.score, last_eval.reasons, last_eval.corrections), self.max_retries + 1


class TaskMemoryStore:
    """In-process task memory abstraction ready for persistent storage integration."""

    def __init__(self):
        self._items: List[TaskMemory] = []

    def remember(self, memory: TaskMemory) -> None:
        self._items.append(memory)

    def recent(self, limit: int = 20) -> List[TaskMemory]:
        return self._items[-max(0, limit):]
