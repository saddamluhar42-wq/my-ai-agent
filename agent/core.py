from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from ai.agent import AgentError, generate


@dataclass
class ExecutionResult:
    answer: str
    success: bool = True
    provider: str = ""
    skill: str = "general"
    metadata: Dict[str, Any] = field(default_factory=dict)


class AgentCore:
    """Simple agent layer around the existing multi-provider AI engine."""

    name = "My AI Agent"
    version = "3.0-simple"

    def run(self, query: str, context: Optional[Dict[str, Any]] = None) -> ExecutionResult:
        query = str(query or "").strip()
        if not query:
            return ExecutionResult(
                answer="Please enter a question.",
                success=False,
                skill="general",
            )

        context = context or {}
        recent_messages = context.get("recent_messages") or []
        memory_context = str(context.get("memory_context") or "").strip()
        file_context = str(context.get("file_context") or "").strip()
        preferred_provider = context.get("preferred_provider")

        sections = [
            "You are My AI Agent.",
            "Answer directly and accurately.",
            "Use the same language and style as the user.",
            "Do not invent facts, actions, sources, or capabilities.",
            "",
            "USER MESSAGE:",
            query,
        ]

        if recent_messages:
            lines = []
            for message in recent_messages[-20:]:
                if isinstance(message, dict) and str(message.get("content") or "").strip():
                    lines.append(
                        f"{str(message.get('role', 'user')).upper()}: {str(message.get('content')).strip()}"
                    )
            if lines:
                sections.extend(["", "RECENT CONVERSATION:", "\n".join(lines)])

        if memory_context:
            sections.extend(["", "MEMORY:", memory_context])

        if file_context:
            sections.extend(["", "UPLOADED FILE CONTEXT:", file_context])

        try:
            result = generate(
                prompt="\n".join(sections),
                preferred_provider=preferred_provider,
            )
        except AgentError:
            raise
        except Exception as exc:
            raise AgentError(f"Agent failed: {exc}") from exc

        answer = str(result.get("answer") or "").strip()
        if not answer:
            raise AgentError("AI engine returned an empty answer.")

        return ExecutionResult(
            answer=answer,
            success=True,
            provider=str(result.get("provider") or ""),
            skill="general",
            metadata={
                "agent_version": self.version,
                "model": str(result.get("model") or ""),
                "research": result.get("research") or {},
            },
        )


_core = AgentCore()


def get_agent_core() -> AgentCore:
    return _core


def run_agent(query: str, context: Optional[Dict[str, Any]] = None) -> ExecutionResult:
    return _core.run(query=query, context=context)
