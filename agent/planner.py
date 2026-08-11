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
    steps: List[PlanStep] = field(default_factory=list)
    requires_memory: bool = True
    requires_verification: bool = False


class AgentPlanner:
    """Create a lightweight validated plan for each user request."""

    def __init__(self):
        self.default_skill = "general_knowledge"

    def create_plan(self, query: str) -> AgentPlan:
        query = str(query or "").strip()

        if not query:
            return self._fallback_plan(query)

        try:
            route = route_query(query)
            steps = self._build_steps(route)
        except Exception:
            return self._fallback_plan(query)

        if not steps:
            return self._fallback_plan(query)

        primary_skill = steps[0].skill_name
        return AgentPlan(
            query=query,
            primary_skill=primary_skill,
            steps=steps,
            requires_memory=True,
            requires_verification=self._needs_verification(steps),
        )

    @staticmethod
    def _build_steps(route: SkillRoute) -> List[PlanStep]:
        steps = []
        order = 1
        used_skills = set()

        primary = AgentPlanner()._validate_skill(
            getattr(route, "primary_skill", None)
        )
        if primary is not None:
            steps.append(
                PlanStep(
                    skill_name=primary.name,
                    purpose=primary.description,
                    order=order,
                )
            )
            used_skills.add(primary.name)
            order += 1

        for skill in getattr(route, "supporting_skills", []) or []:
            validated = AgentPlanner()._validate_skill(skill)
            if validated is None or validated.name in used_skills:
                continue
            steps.append(
                PlanStep(
                    skill_name=validated.name,
                    purpose=validated.description,
                    order=order,
                )
            )
            used_skills.add(validated.name)
            order += 1

        return steps

    @staticmethod
    def _validate_skill(skill):
        if skill is None:
            return None

        skill_name = str(getattr(skill, "name", "") or "").strip()
        if not skill_name:
            return None

        registered = get_skill(skill_name)
        if registered is None or not registered.enabled:
            return None

        return registered

    def _fallback_plan(self, query: str) -> AgentPlan:
        skill = get_skill(self.default_skill)
        purpose = (
            skill.description
            if skill is not None
            else "Handle general questions and requests."
        )

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
    def _needs_verification(steps: List[PlanStep]) -> bool:
        verification_skills = {
            "web_research",
            "coding",
            "file_analysis",
            "image_understanding",
            "image_generation",
            "self_evolution",
        }
        return any(step.skill_name in verification_skills for step in steps)

    def explain_plan(self, plan: AgentPlan) -> str:
        lines = [
            "AGENT PLAN",
            f"Primary skill: {plan.primary_skill}",
            "",
            "Steps:",
        ]

        for step in plan.steps:
            lines.append(
                f"{step.order}. {step.skill_name} — {step.purpose}"
            )

        lines.extend(
            [
                "",
                "Memory: " + ("YES" if plan.requires_memory else "NO"),
                "Verification: " + ("YES" if plan.requires_verification else "NO"),
            ]
        )
        return "\n".join(lines)


planner = AgentPlanner()


def create_plan(query: str) -> AgentPlan:
    return planner.create_plan(query)


def explain_plan(query: str) -> str:
    return planner.explain_plan(create_plan(query))
