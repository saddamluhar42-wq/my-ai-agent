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
    """Fast core agent. Heavy intelligence stays in optional external plugins."""

    name = "My AI Agent"
    version = "3.1-plugin-core"

    def run(self, query: str, context: Optional[Dict[str, Any]] = None) -> ExecutionResult:
        query = str(query or "").strip()
        if not query:
            return ExecutionResult(answer="Please enter a question.", success=False)

        context = context or {}
        recent_messages = context.get("recent_messages") or []
        memory_context = str(context.get("memory_context") or "").strip()
        file_context = str(context.get("file_context") or "").strip()
        preferred_provider = context.get("preferred_provider")
        owner_key = str(context.get("owner_key") or context.get("user_id") or "").strip()

        # Optional external memory plugin. If it is unavailable, the core keeps working normally.
        try:
            from plugins.supabase_memory import memory_text, recall
            if not memory_context and owner_key:
                memory_context = memory_text(recall(owner_key, query, limit=6))
        except Exception:
            pass

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
                    lines.append(f"{str(message.get('role', 'user')).upper()}: {str(message.get('content')).strip()}")
            if lines:
                sections.extend(["", "RECENT CONVERSATION:", "\n".join(lines)])

        if memory_context:
            sections.extend(["", "RELEVANT LONG-TERM MEMORY:", memory_context])

        if file_context:
            sections.extend(["", "UPLOADED FILE CONTEXT:", file_context])

        try:
            result = generate(prompt="\n".join(sections), preferred_provider=preferred_provider)
        except AgentError:
            raise
        except Exception as exc:
            raise AgentError(f"Agent failed: {exc}") from exc

        answer = str(result.get("answer") or "").strip()
        if not answer:
            raise AgentError("AI engine returned an empty answer.")

        # Persist a compact conversation memory asynchronously from the core's point of view.
        # Failures never affect the response path.
        if owner_key:
            try:
                from plugins.supabase_memory import remember
                remember(
                    owner_key,
                    f"User: {query}\nAssistant: {answer}",
                    metadata={"provider": str(result.get("provider") or ""), "model": str(result.get("model") or "")},
                )
            except Exception:
                pass

        return ExecutionResult(
            answer=answer,
            success=True,
            provider=str(result.get("provider") or ""),
            skill="general",
            metadata={
                "agent_version": self.version,
                "model": str(result.get("model") or ""),
                "research": result.get("research") or {},
                "supabase_memory": bool(owner_key),
            },
        )


_core = AgentCore()


def get_agent_core() -> AgentCore:
    return _core


def run_agent(query: str, context: Optional[Dict[str, Any]] = None) -> ExecutionResult:
    return _core.run(query=query, context=context)
