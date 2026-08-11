from typing import Any, Dict, Optional

from agent.executor import ExecutionResult
from agent.planner import create_plan
from ai.agent import AgentError, generate


class AgentCore:
    """
    Main orchestration layer.

    Flow:

        User Request
             ↓
        Planner
             ↓
        Memory / Context
             ↓
        Existing AI Engine
             ↓
        Verification metadata
             ↓
        Final Answer
    """

    def __init__(self):
        self.name = "My AI Agent Core"
        self.version = "1.0.0"

    def run(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> ExecutionResult:

        query = str(query or "").strip()

        if not query:
            return ExecutionResult(
                answer="Please enter a question.",
                success=False,
                skill="general_knowledge",
            )

        context = context or {}

        plan = create_plan(query)

        prompt = self._build_prompt(
            query=query,
            plan=plan,
            context=context,
        )

        try:
            result = generate(
                prompt=prompt
            )

        except AgentError:
            raise

        except Exception as error:
            raise AgentError(
                f"Agent core failed: {error}"
            ) from error

        if not isinstance(result, dict):
            raise AgentError(
                "AI engine returned an invalid result."
            )

        answer = str(
            result.get(
                "answer",
                "",
            )
        ).strip()

        if not answer:
            raise AgentError(
                "AI engine returned an empty answer."
            )

        provider = str(
            result.get(
                "provider",
                "",
            )
            or ""
        )

        return ExecutionResult(
            answer=answer,
            success=True,
            provider=provider,
            skill=plan.primary_skill,
            metadata={
                "agent_version": self.version,
                "primary_skill": (
                    plan.primary_skill
                ),
                "steps": [
                    {
                        "order": step.order,
                        "skill": step.skill_name,
                        "purpose": step.purpose,
                    }
                    for step in plan.steps
                ],
                "requires_memory": (
                    plan.requires_memory
                ),
                "requires_verification": (
                    plan.requires_verification
                ),
            },
        )

    def _build_prompt(
        self,
        query: str,
        plan,
        context: Dict[str, Any],
    ) -> str:

        memory = str(
            context.get(
                "memory_context",
                "",
            )
            or ""
        ).strip()

        file_context = str(
            context.get(
                "file_context",
                "",
            )
            or ""
        ).strip()

        skill_lines = []

        for step in plan.steps:
            skill_lines.append(
                f"{step.order}. "
                f"{step.skill_name}: "
                f"{step.purpose}"
            )

        skills_text = "\n".join(
            skill_lines
        )

        sections = [
            "You are My AI Agent.",
            "",
            "You can reason across multiple capabilities.",
            "Use the available context when relevant.",
            "Do not invent information that is unavailable.",
            "",
            "SELECTED AGENT PLAN:",
            skills_text,
            "",
            "USER QUESTION:",
            query,
        ]

        if memory:
            sections.extend(
                [
                    "",
                    "RELEVANT MEMORY:",
                    memory,
                ]
            )

        if file_context:
            sections.extend(
                [
                    "",
                    "FILE CONTEXT:",
                    file_context,
                ]
            )

        sections.extend(
            [
                "",
                "RESPONSE RULES:",
                "1. Understand the user's actual intent.",
                "2. Use the selected skill appropriately.",
                "3. Use memory only when relevant.",
                "4. If information is uncertain, say so.",
                "5. Do not fabricate sources or facts.",
                "6. Give a direct and useful answer.",
                "7. If the task requires a tool that is not",
                "   available, clearly state that limitation.",
            ]
        )

        return "\n".join(sections)


_core = AgentCore()


def run_agent(
    query: str,
    context: Optional[Dict[str, Any]] = None,
) -> ExecutionResult:

    return _core.run(
        query=query,
        context=context,
    )


def get_agent_core() -> AgentCore:
    return _core
