"""Bounded autonomous task planning and execution primitives."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class TaskStatus(str, Enum):
    PLANNED = "planned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass
class TaskStep:
    id: str
    description: str
    tool: Optional[str] = None
    args: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    requires_confirmation: bool = False
    status: TaskStatus = TaskStatus.PLANNED
    result: Any = None
    error: Optional[str] = None


@dataclass
class TaskPlan:
    goal: str
    steps: List[TaskStep]
    max_steps: int = 12


class TaskExecutor:
    """Execute approved plans with hard bounds and explicit tool allowlists."""

    def __init__(self, tools: Optional[Dict[str, Callable[..., Any]]] = None):
        self.tools = tools or {}

    def validate(self, plan: TaskPlan) -> None:
        if not plan.goal.strip():
            raise ValueError("Task goal cannot be empty")
        if not plan.steps:
            raise ValueError("Task plan must contain at least one step")
        if len(plan.steps) > plan.max_steps:
            raise ValueError(f"Plan exceeds maximum of {plan.max_steps} steps")
        ids = {s.id for s in plan.steps}
        for step in plan.steps:
            if any(dep not in ids for dep in step.depends_on):
                raise ValueError(f"Unknown dependency in step {step.id}")

    def execute(self, plan: TaskPlan, *, allow_actions: bool = False) -> TaskPlan:
        self.validate(plan)
        completed = set()
        for step in plan.steps:
            if any(dep not in completed for dep in step.depends_on):
                step.status = TaskStatus.BLOCKED
                step.error = "Dependency not completed"
                continue
            if step.requires_confirmation and not allow_actions:
                step.status = TaskStatus.BLOCKED
                step.error = "Explicit confirmation required"
                continue
            step.status = TaskStatus.RUNNING
            try:
                if not step.tool:
                    step.result = {"status": "planned", "description": step.description}
                elif step.tool not in self.tools:
                    raise RuntimeError(f"Tool not allowlisted: {step.tool}")
                else:
                    step.result = self.tools[step.tool](**step.args)
                step.status = TaskStatus.COMPLETED
                completed.add(step.id)
            except Exception as exc:
                step.status = TaskStatus.FAILED
                step.error = str(exc)
        return plan
