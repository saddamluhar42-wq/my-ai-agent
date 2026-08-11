from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from agent.planner import (
    AgentPlan,
    PlanStep,
    create_plan,
)


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
    Executes an AgentPlan through registered
    skill handlers.

    The executor supports:

    - primary skill execution
    - supporting skill execution
    - shared context
    - structured execution metadata
    - graceful handler failures
    - runtime skill registration
    """

    def __init__(self):
        self._handlers: Dict[
            str,
            Callable,
        ] = {}

    # ========================================================
    # HANDLER REGISTRATION
    # ========================================================

    def register_handler(
        self,
        skill_name: str,
        handler,
    ):
        skill_name = str(
            skill_name or ""
        ).strip()

        if not skill_name:
            raise ValueError(
                "skill_name is required."
            )

        if not callable(handler):
            raise TypeError(
                "handler must be callable."
            )

        self._handlers[
            skill_name
        ] = handler

    def unregister_handler(
        self,
        skill_name: str,
    ) -> bool:

        skill_name = str(
            skill_name or ""
        ).strip()

        if skill_name not in self._handlers:
            return False

        del self._handlers[
            skill_name
        ]

        return True

    def has_handler(
        self,
        skill_name: str,
    ) -> bool:

        return (
            str(
                skill_name or ""
            ).strip()
            in self._handlers
        )

    def get_registered_skills(
        self,
    ) -> List[str]:

        return sorted(
            self._handlers.keys()
        )

    # ========================================================
    # SINGLE HANDLER EXECUTION
    # ========================================================

    def _run_handler(
        self,
        skill_name: str,
        query: str,
        plan: AgentPlan,
        context: Dict[str, Any],
    ) -> ExecutionResult:

        handler = self._handlers.get(
            skill_name
        )

        if handler is None:

            return ExecutionResult(
                answer="",
                success=False,
                skill=skill_name,
                metadata={
                    "error": (
                        "No executor registered "
                        f"for skill: {skill_name}"
                    ),
                },
            )

        try:

            result = handler(
                query=query,
                plan=plan,
                context=context,
            )

        except Exception as error:

            return ExecutionResult(
                answer="",
                success=False,
                skill=skill_name,
                metadata={
                    "error": str(error),
                    "exception_type": (
                        type(error).__name__
                    ),
                },
            )

        return self._normalize_result(
            result=result,
            skill_name=skill_name,
        )

    # ========================================================
    # RESULT NORMALIZATION
    # ========================================================

    def _normalize_result(
        self,
        result,
        skill_name: str,
    ) -> ExecutionResult:

        if isinstance(
            result,
            ExecutionResult,
        ):

            if not result.skill:
                result.skill = skill_name

            return result

        if isinstance(
            result,
            dict,
        ):

            metadata = result.get(
                "metadata",
                {},
            )

            if not isinstance(
                metadata,
                dict,
            ):
                metadata = {
                    "raw_metadata": str(
                        metadata
                    )
                }

            return ExecutionResult(
                answer=str(
                    result.get(
                        "answer",
                        "",
                    )
                    or ""
                ).strip(),
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
                    or ""
                ),
                skill=str(
                    result.get(
                        "skill",
                        skill_name,
                    )
                    or skill_name
                ),
                metadata=metadata,
            )

        return ExecutionResult(
            answer=str(
                result or ""
            ).strip(),
            success=True,
            skill=skill_name,
        )

    # ========================================================
    # PLAN EXECUTION
    # ========================================================

    def execute(
        self,
        plan: AgentPlan,
        context: Optional[
            Dict[str, Any]
        ] = None,
    ) -> ExecutionResult:

        if plan is None:

            return ExecutionResult(
                answer="",
                success=False,
                metadata={
                    "error": (
                        "Agent plan is required."
                    ),
                },
            )

        context = dict(
            context or {}
        )

        execution_log = []

        successful_results = []

        steps = list(
            plan.steps or []
        )

        if not steps:

            return ExecutionResult(
                answer="",
                success=False,
                skill=plan.primary_skill,
                metadata={
                    "error": (
                        "Agent plan contains "
                        "no executable steps."
                    ),
                },
            )

        # ----------------------------------------------------
        # Execute primary first, then supporting skills.
        # ----------------------------------------------------

        for step in steps:

            if not isinstance(
                step,
                PlanStep,
            ):
                continue

            skill_name = str(
                step.skill_name or ""
            ).strip()

            if not skill_name:
                continue

            result = self._run_handler(
                skill_name=skill_name,
                query=plan.query,
                plan=plan,
                context=context,
            )

            execution_log.append(
                {
                    "order": step.order,
                    "skill": skill_name,
                    "success": result.success,
                    "provider": result.provider,
                    "error": result.metadata.get(
                        "error"
                    ),
                }
            )

            if result.success:

                successful_results.append(
                    result
                )

                # Allow later skills to use
                # earlier execution results.
                context[
                    f"skill_result:{skill_name}"
                ] = result

            # Primary skill failure should stop
            # execution unless another step can
            # meaningfully continue.
            if (
                step.order == 1
                and not result.success
            ):

                return ExecutionResult(
                    answer="",
                    success=False,
                    provider=result.provider,
                    skill=plan.primary_skill,
                    metadata={
                        "error": result.metadata.get(
                            "error",
                            "Primary skill failed.",
                        ),
                        "execution_log": execution_log,
                    },
                )

        if not successful_results:

            return ExecutionResult(
                answer="",
                success=False,
                skill=plan.primary_skill,
                metadata={
                    "error": (
                        "No skill handler "
                        "produced a result."
                    ),
                    "execution_log": execution_log,
                },
            )

        # ----------------------------------------------------
        # Final result is the primary result unless it
        # produced no answer, then use the latest useful
        # supporting result.
        # ----------------------------------------------------

        primary_result = (
            successful_results[0]
        )

        final_result = primary_result

        if not primary_result.answer:

            for result in reversed(
                successful_results
            ):

                if result.answer:

                    final_result = result
                    break

        metadata = dict(
            final_result.metadata or {}
        )

        metadata[
            "execution_log"
        ] = execution_log

        metadata[
            "executed_skills"
        ] = [
            item["skill"]
            for item in execution_log
            if item["success"]
        ]

        metadata[
            "failed_skills"
        ] = [
            item["skill"]
            for item in execution_log
            if not item["success"]
        ]

        return ExecutionResult(
            answer=final_result.answer,
            success=bool(
                final_result.success
            ),
            provider=final_result.provider,
            skill=plan.primary_skill,
            metadata=metadata,
        )

    # ========================================================
    # QUERY EXECUTION
    # ========================================================

    def execute_query(
        self,
        query: str,
        context: Optional[
            Dict[str, Any]
        ] = None,
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

        plan = create_plan(
            query
        )

        return self.execute(
            plan,
            context=context,
        )


# ============================================================
# GLOBAL EXECUTOR
# ============================================================

executor = AgentExecutor()


# ============================================================
# PUBLIC API
# ============================================================

def register_skill_handler(
    skill_name: str,
    handler,
):
    executor.register_handler(
        skill_name,
        handler,
    )


def unregister_skill_handler(
    skill_name: str,
) -> bool:

    return executor.unregister_handler(
        skill_name
    )


def execute_query(
    query: str,
    context: Optional[
        Dict[str, Any]
    ] = None,
) -> ExecutionResult:

    return executor.execute_query(
        query,
        context=context,
    )


def get_registered_skills() -> List[str]:

    return executor.get_registered_skills()
