from dataclasses import dataclass, field
from typing import List

from skills.registry import get_skill
from skills.router import SkillRoute, route_query


@dataclass
class PlanStep:
    skill_name: str
    purpose: str
    order: int


@dataclass
class AgentPlan:
    query: str
    primary_skill: str
    steps: List[PlanStep] = field(
        default_factory=list
    )
    requires_memory: bool = True
    requires_verification: bool = False


class AgentPlanner:
    """
    Converts a user request into an executable
    multi-skill plan.

    The planner uses the Skill Router first and
    validates every selected skill against the
    central Skill Registry.
    """

    def __init__(self):
        self.default_skill = "general_knowledge"

    def create_plan(
        self,
        query: str,
    ) -> AgentPlan:

        query = str(
            query or ""
        ).strip()

        if not query:
            return AgentPlan(
                query="",
                primary_skill=self.default_skill,
                steps=[
                    PlanStep(
                        skill_name=self.default_skill,
                        purpose=(
                            "Handle general questions "
                            "and requests."
                        ),
                        order=1,
                    )
                ],
                requires_memory=True,
                requires_verification=False,
            )

        try:
            route = route_query(
                query
            )

        except Exception:
            return self._fallback_plan(
                query
            )

        steps = self._build_steps(
            route
        )

        if not steps:
            return self._fallback_plan(
                query
            )

        primary_skill = (
            steps[0].skill_name
        )

        return AgentPlan(
            query=query,
            primary_skill=primary_skill,
            steps=steps,
            requires_memory=True,
            requires_verification=(
                self._needs_verification(
                    steps
                )
            ),
        )

    def _build_steps(
        self,
        route: SkillRoute,
    ) -> List[PlanStep]:

        steps = []

        order = 1
        used_skills = set()

        # ----------------------------------------------------
        # PRIMARY SKILL
        # ----------------------------------------------------

        primary = self._validate_skill(
            getattr(
                route,
                "primary_skill",
                None,
            )
        )

        if primary is not None:

            steps.append(
                PlanStep(
                    skill_name=primary.name,
                    purpose=primary.description,
                    order=order,
                )
            )

            used_skills.add(
                primary.name
            )

            order += 1

        # ----------------------------------------------------
        # SUPPORTING SKILLS
        # ----------------------------------------------------

        supporting_skills = getattr(
            route,
            "supporting_skills",
            [],
        )

        for skill in supporting_skills:

            validated = (
                self._validate_skill(
                    skill
                )
            )

            if validated is None:
                continue

            if (
                validated.name
                in used_skills
            ):
                continue

            steps.append(
                PlanStep(
                    skill_name=validated.name,
                    purpose=validated.description,
                    order=order,
                )
            )

            used_skills.add(
                validated.name
            )

            order += 1

        return steps

    def _validate_skill(
        self,
        skill,
    ):
        """
        Validate router output against
        the central Skill Registry.
        """

        if skill is None:
            return None

        skill_name = str(
            getattr(
                skill,
                "name",
                "",
            )
            or ""
        ).strip()

        if not skill_name:
            return None

        registered = get_skill(
            skill_name
        )

        if registered is None:
            return None

        if not registered.enabled:
            return None

        return registered

    def _fallback_plan(
        self,
        query: str,
    ) -> AgentPlan:

        skill = get_skill(
            self.default_skill
        )

        if skill is None:

            purpose = (
                "Handle general questions "
                "and requests."
            )

        else:

            purpose = skill.description

        step = PlanStep(
            skill_name=self.default_skill,
            purpose=purpose,
            order=1,
        )

        return AgentPlan(
            query=query,
            primary_skill=self.default_skill,
            steps=[step],
            requires_memory=True,
            requires_verification=False,
        )

    @staticmethod
    def _needs_verification(
        steps: List[PlanStep],
    ) -> bool:

        verification_skills = {
            "web_research",
            "coding",
            "file_analysis",
            "image_understanding",
            "image_generation",
            "self_evolution",
        }

        return any(
            step.skill_name
            in verification_skills
            for step in steps
        )

    def explain_plan(
        self,
        plan: AgentPlan,
    ) -> str:

        lines = [
            "AGENT PLAN",
            f"Primary skill: {plan.primary_skill}",
            "",
            "Steps:",
        ]

        for step in plan.steps:

            lines.append(
                f"{step.order}. "
                f"{step.skill_name} — "
                f"{step.purpose}"
            )

        lines.extend(
            [
                "",
                "Memory: "
                + (
                    "YES"
                    if plan.requires_memory
                    else "NO"
                ),
                "Verification: "
                + (
                    "YES"
                    if plan.requires_verification
                    else "NO"
                ),
            ]
        )

        return "\n".join(
            lines
        )


# ============================================================
# GLOBAL PLANNER
# ============================================================

planner = AgentPlanner()


# ============================================================
# PUBLIC API
# ============================================================

def create_plan(
    query: str,
) -> AgentPlan:

    return planner.create_plan(
        query
    )


def explain_plan(
    query: str,
) -> str:

    plan = create_plan(
        query
    )

    return planner.explain_plan(
        plan
    )
