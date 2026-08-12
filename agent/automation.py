"""Safe autonomous workflow execution for My AI Agent.

The engine plans a request into a small set of validated actions, executes only
registered capabilities, and keeps external side effects behind an explicit
approval flag. This makes automation deterministic and auditable instead of
letting an LLM invent tool calls.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from ai.agent import AgentError, generate, research_web


@dataclass
class AutomationStep:
    action: str
    input: str
    reason: str = ""
    requires_approval: bool = False


@dataclass
class AutomationResult:
    success: bool
    goal: str
    steps: List[Dict[str, Any]] = field(default_factory=list)
    answer: str = ""
    errors: List[str] = field(default_factory=list)


class AutomationEngine:
    """Plan -> validate -> execute -> report workflow engine."""

    SAFE_ACTIONS = {"answer", "research", "remember"}
    SIDE_EFFECT_ACTIONS = {"schedule", "send", "write", "delete", "deploy"}
    ALLOWED_ACTIONS = SAFE_ACTIONS | SIDE_EFFECT_ACTIONS

    def __init__(self) -> None:
        self._handlers: Dict[str, Callable[..., Any]] = {
            "answer": self._answer,
            "research": self._research,
            "remember": self._remember,
        }

    def plan(self, goal: str) -> List[AutomationStep]:
        """Create a conservative plan. Unknown model-generated actions are rejected."""
        text = str(goal or "").strip()
        if not text:
            raise AgentError("Automation goal cannot be empty.")

        # Fast deterministic plans cover common automation patterns without an
        # extra model call. The model is only used for genuinely multi-step goals.
        parts = [p.strip() for p in re.split(r"\b(?:then|phir|and then|uske baad)\b", text, flags=re.I) if p.strip()]
        if len(parts) == 1:
            parts = [p.strip() for p in re.split(r"\s+(?:and|aur)\s+", text, flags=re.I) if p.strip()]

        steps: List[AutomationStep] = []
        for part in parts[:6]:
            low = part.lower()
            if any(x in low for x in ("search", "research", "latest", "current", "news", "find out", "check online")):
                steps.append(AutomationStep("research", part, "live information requested"))
            elif any(x in low for x in ("remember", "save to memory", "store this")):
                steps.append(AutomationStep("remember", part, "persistent memory requested"))
            elif any(x in low for x in ("remind", "schedule", "at ", "tomorrow", "kal ")):
                steps.append(AutomationStep("schedule", part, "scheduled action requested", True))
            elif any(x in low for x in ("send", "email", "message", "post", "deploy", "delete", "write to")):
                steps.append(AutomationStep("send", part, "external side effect requested", True))
            else:
                steps.append(AutomationStep("answer", part, "reasoning/output step"))

        if not steps:
            steps = [AutomationStep("answer", text, "default response")]
        return steps

    def execute(self, goal: str, *, context: Optional[Dict[str, Any]] = None, approved: bool = False) -> AutomationResult:
        context = context or {}
        steps = self.plan(goal)
        report: List[Dict[str, Any]] = []
        errors: List[str] = []
        outputs: List[str] = []

        for index, step in enumerate(steps, 1):
            record = {"step": index, "action": step.action, "input": step.input, "status": "pending"}
            if step.action not in self.ALLOWED_ACTIONS:
                record.update(status="rejected", error="Action is not registered.")
                errors.append(f"Step {index}: unsupported action {step.action}")
                report.append(record)
                continue
            if step.requires_approval and not approved:
                record.update(status="approval_required", reason=step.reason)
                report.append(record)
                continue
            handler = self._handlers.get(step.action)
            if handler is None:
                record.update(status="not_implemented", reason="This connector is not configured in this deployment.")
                report.append(record)
                continue
            try:
                result = handler(step.input, context)
                text = str(result or "").strip()
                record.update(status="completed", output=text[:2000])
                if text:
                    outputs.append(text)
            except Exception as exc:
                message = str(exc)[:1000]
                record.update(status="failed", error=message)
                errors.append(f"Step {index}: {message}")
            report.append(record)

        completed = sum(1 for item in report if item["status"] == "completed")
        approval = [item for item in report if item["status"] == "approval_required"]
        if approval and not errors:
            headline = f"Automation paused: {completed}/{len(report)} steps completed. Approval is required for side effects."
        elif errors:
            headline = f"Automation completed with issues: {completed}/{len(report)} steps completed."
        else:
            headline = f"Automation completed: {completed}/{len(report)} steps completed."
        answer = headline
        if outputs:
            answer += "\n\n" + "\n\n".join(outputs)
        if errors:
            answer += "\n\nErrors:\n- " + "\n- ".join(errors)
        return AutomationResult(success=not errors, goal=goal, steps=report, answer=answer, errors=errors)

    def _answer(self, text: str, context: Dict[str, Any]) -> str:
        result = generate(
            prompt=("Respond to this automation step. Return only the useful user-facing result.\n\n" + text),
            preferred_provider=context.get("preferred_provider"),
            route_capability="general",
        )
        return str(result.get("answer") or "").strip()

    def _research(self, text: str, context: Dict[str, Any]) -> str:
        result = research_web(text, deep=bool(context.get("deep_research")))
        evidence = str(result.get("evidence") or "").strip()
        return evidence[:12000] if evidence else "Research returned no usable sources."

    def _remember(self, text: str, context: Dict[str, Any]) -> str:
        owner_key = str(context.get("owner_key") or "").strip()
        if not owner_key:
            return "Memory step skipped: no user identity is configured."
        from plugins.supabase_memory import remember
        remember(owner_key, text, metadata={"source": "automation"})
        return "Saved to long-term memory."


_engine = AutomationEngine()


def get_automation_engine() -> AutomationEngine:
    return _engine


def run_automation(goal: str, *, context: Optional[Dict[str, Any]] = None, approved: bool = False) -> AutomationResult:
    return _engine.execute(goal, context=context, approved=approved)
