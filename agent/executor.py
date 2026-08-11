from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from agent.planner import (
    AgentPlan,
    PlanStep,
    create_plan,
)

from skills.video_generation import (
    generate_video,
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

    Supports:

    - primary skill execution
    - supporting skill execution
    - shared context
    - structured execution metadata
    - graceful handler failures
    - runtime skill registration
    - built-in AI video generation
    """

    def __init__(self):
        self._handlers: Dict[
            str,
            Callable,
        ] = {}

        self._register_builtin_handlers()

    # ========================================================
    # BUILT-IN HANDLERS
    # ========================================================

    def _register_builtin_handlers(self):
        """
        Register built-in agent capabilities.
        """

        self.register_handler(
            "video_generation",
            self._handle_video_generation,
        )

    # ========================================================
    # VIDEO GENERATION
    # ========================================================

    def _handle_video_generation(
        self,
        query: str,
        plan: AgentPlan,
        context: Dict[str, Any],
    ) -> ExecutionResult:

        video_prompt = str(
            context.get(
                "video_prompt",
                query,
            )
            or query
        ).strip()

        duration = self._safe_int(
            context.get(
                "video_duration",
                5,
            ),
            default=5,
            minimum=1,
            maximum=300,
        )

        aspect_ratio = str(
            context.get(
                "video_aspect_ratio",
                "16:9",
            )
            or "16:9"
        ).strip()

        style = str(
            context.get(
                "video_style",
                "cinematic",
            )
            or "cinematic"
        ).strip()

        negative_prompt = str(
            context.get(
                "video_negative_prompt",
                "",
            )
            or ""
        ).strip()

        image_input = context.get(
            "video_image_input"
        )

        provider = context.get(
            "video_provider"
        )

        result = generate_video(
            prompt=video_prompt,
            duration=duration,
            aspect_ratio=aspect_ratio,
            style=style,
            image_input=image_input,
            negative_prompt=negative_prompt,
            provider=provider,
            metadata={
                "source": "agent_executor",
                "query": query,
            },
        )

        metadata = dict(
            result.metadata or {}
        )

        metadata.update(
            {
                "video_prompt": video_prompt,
                "duration": duration,
                "aspect_ratio": aspect_ratio,
                "style": style,
            }
        )

        if not result.success:

            return ExecutionResult(
                answer=(
                    "Video generation could not be "
                    "completed. "
                    f"{result.error}"
                ).strip(),
                success=False,
                provider=result.provider,
                skill="video_generation",
                metadata={
                    **metadata,
                    "status": result.status,
                    "job_id": result.job_id,
                    "error": result.error,
                },
            )

        answer = (
            "AI video generation completed."
        )

        if result.video_url:
            answer += (
                f"\nVideo: {result.video_url}"
            )

        return ExecutionResult(
            answer=answer,
            success=True,
            provider=result.provider,
            skill="video_generation",
            metadata={
                **metadata,
                "status": result.status,
                "job_id": result.job_id,
                "video_url": result.video_url,
            },
        )

    @staticmethod
    def _safe_int(
        value,
        default: int,
        minimum: int,
        maximum: int,
    ) -> int:

        try:
            value = int(value)
        except (
            TypeError,
            ValueError,
        ):
            value = default

        return max(
            minimum,
            min(
                value,
                maximum,
            ),
        )

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

                context[
                    f"skill_result:{skill_name}"
                ] = result

            if (
                step.order == 1
                and not result.success
            ):

                return ExecutionResult(
                    answer=result.answer,
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
        # Final result
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
