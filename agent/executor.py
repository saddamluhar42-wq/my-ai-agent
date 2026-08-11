from dataclasses import dataclass, field
from typing import Any, Dict, List

from agent.planner import AgentPlan, create_plan


@dataclass
class ExecutionResult:
    answer: str
    success: bool = True
    provider: str = ""
    skill: str = ""
    metadata: Dict[str, Any] = field(
        default_factory=dict
    )


class AgentExecutor:
    """
    Executes an AgentPlan.

    This layer is intentionally separated from
    routing and planning so individual skills can
    be connected without rewriting the agent core.
    """

    def __init__(self):
        self._handlers = {}

    def register_handler(
        self,
        skill_name: str,
        handler,
    ):
        if not skill_name:
            raise ValueError(
                "skill_name is required."
            )

        if not callable(handler):
            raise TypeError(
                "handler must be callable."
            )

        self._handlers[skill_name] = handler

    def has_handler(
        self,
        skill_name: str,
    ) -> bool:
        return skill_name in self._handlers

    def execute(
        self,
        plan: AgentPlan,
        context: Dict[str, Any] | None = None,
    ) -> ExecutionResult:

        context = context or {}

        primary_skill = plan.primary_skill

        handler = self._handlers.get(
            primary_skill
        )

        if handler is None:
            return ExecutionResult(
                answer="",
                success=False,
                skill=primary_skill,
                metadata={
                    "error": (
                        f"No executor registered for "
                        f"skill: {primary_skill}"
                    ),
                },
            )

        try:
            result = handler(
                query=plan.query,
                plan=plan,
                context=context,
            )

            if isinstance(
                result,
                ExecutionResult,
            ):
                return result

            if isinstance(
                result,
                dict,
            ):
                return ExecutionResult(
                    answer=str(
                        result.get(
                            "answer",
                            "",
                        )
                    ),
                    success=bool(
                        result.get(
                            "success",
                            True,
                        )
                    ),
                    provider=str(
                        result.get(
                            "provider",
                            "",
                        )
                    ),
                    skill=primary_skill,
                    metadata=result.get(
                        "metadata",
                        {},
                    ),
                )

            return ExecutionResult(
                answer=str(result or ""),
                success=True,
                skill=primary_skill,
            )

        except Exception as error:
            return ExecutionResult(
                answer="",
                success=False,
                skill=primary_skill,
                metadata={
                    "error": str(error),
                },
            )

    def execute_query(
        self,
        query: str,
        context: Dict[str, Any] | None = None,
    ) -> ExecutionResult:

        plan = create_plan(query)

        return self.execute(
            plan,
            context=context,
        )

    def get_registered_skills(
        self,
    ) -> List[str]:

        return sorted(
            self._handlers.keys()
        )


executor = AgentExecutor()


def register_skill_handler(
    skill_name: str,
    handler,
):
    executor.register_handler(
        skill_name,
        handler,
    )


def execute_query(
    query: str,
    context: Dict[str, Any] | None = None,
) -> ExecutionResult:

    return executor.execute_query(
        query,
        context=context,
    )
