from typing import Any, Dict, Optional

from agent.evolution import evolve_from_interaction
from agent.executor import ExecutionResult
from agent.knowledge import build_knowledge_context
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
        Memory
             ↓
        Persistent Knowledge
             ↓
        File Context
             ↓
        Existing AI Engine
             ↓
        Final Answer
             ↓
        Evolution Engine
             ↓
        Persistent Learning
    """

    def __init__(self):

        self.name = "My AI Agent Core"
        self.version = "1.1.0"

        self.evolution_enabled = True

    def run(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> ExecutionResult:

        query = str(
            query or ""
        ).strip()

        if not query:

            return ExecutionResult(
                answer="Please enter a question.",
                success=False,
                skill="general_knowledge",
            )

        context = context or {}

        plan = create_plan(
            query
        )

        user_id = context.get(
            "user_id"
        )

        # ----------------------------------------------------
        # MEMORY
        # ----------------------------------------------------

        memory_context = str(
            context.get(
                "memory_context",
                "",
            )
            or ""
        ).strip()

        # ----------------------------------------------------
        # PERSISTENT KNOWLEDGE
        # ----------------------------------------------------

        knowledge_context = ""

        try:

            knowledge_context = (
                build_knowledge_context(
                    user_id=user_id,
                    query=query,
                    limit=20,
                )
            )

        except Exception:
            # Knowledge must never break normal AI chat.
            knowledge_context = ""

        # ----------------------------------------------------
        # FILE CONTEXT
        # ----------------------------------------------------

        file_context = str(
            context.get(
                "file_context",
                "",
            )
            or ""
        ).strip()

        # ----------------------------------------------------
        # RECENT MESSAGES
        # ----------------------------------------------------

        recent_messages = context.get(
            "recent_messages",
            [],
        )

        # ----------------------------------------------------
        # PROVIDER PREFERENCE
        # ----------------------------------------------------

        preferred_provider = context.get(
            "preferred_provider"
        )

        # ----------------------------------------------------
        # BUILD AI PROMPT
        # ----------------------------------------------------

        prompt = self._build_prompt(
            query=query,
            plan=plan,
            memory_context=memory_context,
            knowledge_context=knowledge_context,
            file_context=file_context,
            recent_messages=recent_messages,
            preferred_provider=preferred_provider,
        )

        # ----------------------------------------------------
        # AI GENERATION
        # ----------------------------------------------------

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

        if not isinstance(
            result,
            dict,
        ):

            raise AgentError(
                "AI engine returned an invalid result."
            )

        answer = str(
            result.get(
                "answer",
                "",
            )
            or ""
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

        model = str(
            result.get(
                "model",
                "",
            )
            or ""
        )

        # ----------------------------------------------------
        # SELF EVOLUTION
        # ----------------------------------------------------

        evolution_result = {
            "enabled": False,
            "learned": [],
            "count": 0,
        }

        if (
            self.evolution_enabled
            and user_id is not None
        ):

            try:

                evolution_result = (
                    evolve_from_interaction(
                        user_id=user_id,
                        query=query,
                        answer=answer,
                    )
                )

            except Exception as error:

                evolution_result = {
                    "enabled": True,
                    "learned": [],
                    "count": 0,
                    "error": str(error),
                }

        # ----------------------------------------------------
        # RESULT
        # ----------------------------------------------------

        metadata = {
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

            "model": model,

            "knowledge_used": bool(
                knowledge_context
            ),

            "evolution": evolution_result,
        }

        return ExecutionResult(
            answer=answer,
            success=True,
            provider=provider,
            skill=plan.primary_skill,
            metadata=metadata,
        )

    def _build_prompt(
        self,
        query: str,
        plan,
        memory_context: str,
        knowledge_context: str,
        file_context: str,
        recent_messages,
        preferred_provider=None,
    ) -> str:

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

            "You are a general-purpose intelligent AI agent.",

            "You should understand the user's actual goal "
            "before answering.",

            "Use available memory, persistent knowledge, "
            "files, and conversation context when relevant.",

            "Do not invent facts, sources, files, tool results, "
            "or capabilities.",

            "",

            "SELECTED AGENT PLAN:",

            skills_text,

            "",

            "USER QUESTION:",

            query,
        ]

        # ----------------------------------------------------
        # PERSISTENT KNOWLEDGE
        # ----------------------------------------------------

        if knowledge_context:

            sections.extend(
                [
                    "",
                    "PERSISTENT KNOWLEDGE:",
                    knowledge_context,
                ]
            )

        # ----------------------------------------------------
        # CONVERSATION MEMORY
        # ----------------------------------------------------

        if memory_context:

            sections.extend(
                [
                    "",
                    "RELEVANT CONVERSATION MEMORY:",
                    memory_context,
                ]
            )

        # ----------------------------------------------------
        # RECENT MESSAGES
        # ----------------------------------------------------

        if recent_messages:

            recent_lines = []

            for message in recent_messages:

                if not isinstance(
                    message,
                    dict,
                ):
                    continue

                role = str(
                    message.get(
                        "role",
                        "",
                    )
                ).upper()

                content = str(
                    message.get(
                        "content",
                        "",
                    )
                    or ""
                ).strip()

                if not content:
                    continue

                recent_lines.append(
                    f"{role}: {content}"
                )

            if recent_lines:

                sections.extend(
                    [
                        "",
                        "RECENT CONVERSATION:",
                        "\n".join(
                            recent_lines
                        ),
                    ]
                )

        # ----------------------------------------------------
        # FILE CONTEXT
        # ----------------------------------------------------

        if file_context:

            sections.extend(
                [
                    "",
                    "UPLOADED FILE CONTEXT:",
                    file_context,
                ]
            )

        # ----------------------------------------------------
        # PROVIDER
        # ----------------------------------------------------

        if preferred_provider:

            sections.extend(
                [
                    "",
                    "PREFERRED AI PROVIDER:",
                    str(
                        preferred_provider
                    ),
                ]
            )

        # ----------------------------------------------------
        # BEHAVIOR
        # ----------------------------------------------------

        sections.extend(
            [
                "",
                "CORE BEHAVIOR:",
                "1. Understand intent before answering.",
                "2. Give the most useful answer possible.",
                "3. Use relevant persistent knowledge.",
                "4. Use relevant conversation memory.",
                "5. Use uploaded files when they are relevant.",
                "6. Do not blindly trust old memory.",
                "7. Do not fabricate missing information.",
                "8. Clearly distinguish facts from uncertainty.",
                "9. If a task needs external information "
                "and no tool is available, say so.",
                "10. Keep the answer appropriate to the user's request.",
                "",
                "SELF-EVOLUTION:",
                "The agent has a persistent learning system.",
                "After answering, useful interaction information "
                "may be evaluated for future retention.",
                "Do not claim that you learned something permanently "
                "unless the system actually stored it.",
            ]
        )

        return "\n".join(
            sections
        )


# ============================================================
# GLOBAL CORE
# ============================================================

_core = AgentCore()


# ============================================================
# PUBLIC API
# ============================================================

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


def set_evolution_enabled(
    enabled: bool,
):

    _core.evolution_enabled = bool(
        enabled
    )


def is_evolution_enabled() -> bool:

    return bool(
        _core.evolution_enabled
    )
