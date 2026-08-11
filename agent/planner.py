from dataclasses import dataclass, field
from typing import List

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
    """

    def create_plan(
        self,
        query: str,
    ) -> AgentPlan:

        route = route_query(query)

        steps = self._build_steps(route)

        return AgentPlan(
            query=query.strip(),
            primary_skill=(
                route.primary_skill.name
            ),
            steps=steps,
            requires_memory=True,
            requires_verification=(
                self._needs_verification(route)
            ),
        )

    def _build_steps(
        self,
        route: SkillRoute,
    ) -> List[PlanStep]:

        steps = []

        order = 1

        steps.append(
            PlanStep(
                skill_name=route.primary_skill.name,
                purpose=(
                    route.primary_skill.description
                ),
                order=order,
            )
        )

        order += 1

        for skill in route.supporting_skills:
            steps.append(
                PlanStep(
                    skill_name=skill.name,
                    purpose=skill.description,
                    order=order,
                )
            )

            order += 1

        return steps

    @staticmethod
    def _needs_verification(
        route: SkillRoute,
    ) -> bool:

        verification_skills = {
            "web_research",
            "coding",
            "file_analysis",
            "image_understanding",
            "self_evolution",
        }

        if (
            route.primary_skill.name
            in verification_skills
        ):
            return True

        return any(
            skill.name in verification_skills
            for skill in route.supporting_skills
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
                f"Memory: "
                f"{'YES' if plan.requires_memory else 'NO'}",
                f"Verification: "
                f"{'YES' if plan.requires_verification else 'NO'}",
            ]
        )

        return "\n".join(lines)


planner = AgentPlanner()


def create_plan(
    query: str,
) -> AgentPlan:
    return planner.create_plan(query)


def explain_plan(
    query: str,
) -> str:

    plan = create_plan(query)

    return planner.explain_plan(plan)
