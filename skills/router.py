from dataclasses import dataclass
from typing import List

from skills.registry import Skill, registry


@dataclass
class SkillRoute:
    primary_skill: Skill
    supporting_skills: List[Skill]


class SkillRouter:
    """
    Automatically selects the most appropriate skills
    for an incoming user request.
    """

    def __init__(self, skill_registry=None):
        self.registry = skill_registry or registry

    def route(
        self,
        query: str,
        max_supporting_skills: int = 3,
    ) -> SkillRoute:
        matches = self.registry.find_matches(
            query,
            limit=max_supporting_skills + 1,
        )

        if not matches:
            general = self.registry.get(
                "general_knowledge"
            )

            return SkillRoute(
                primary_skill=general,
                supporting_skills=[],
            )

        primary = matches[0]

        supporting = [
            skill
            for skill in matches[1:]
            if skill.name != primary.name
        ]

        return SkillRoute(
            primary_skill=primary,
            supporting_skills=supporting[
                :max_supporting_skills
            ],
        )

    def explain_route(
        self,
        query: str,
    ) -> str:
        route = self.route(query)

        lines = [
            "SKILL ROUTING",
            f"Primary: {route.primary_skill.name}",
        ]

        if route.supporting_skills:
            lines.append("Supporting:")

            for skill in route.supporting_skills:
                lines.append(
                    f"- {skill.name}"
                )

        return "\n".join(lines)

    def build_agent_instruction(
        self,
        query: str,
    ) -> str:
        route = self.route(query)

        lines = [
            "SELECTED SKILL:",
            route.primary_skill.name,
            "",
            "SKILL PURPOSE:",
            route.primary_skill.description,
        ]

        if route.supporting_skills:
            lines.extend(
                [
                    "",
                    "SUPPORTING SKILLS:",
                ]
            )

            for skill in route.supporting_skills:
                lines.append(
                    f"- {skill.name}: "
                    f"{skill.description}"
                )

        lines.extend(
            [
                "",
                "USER REQUEST:",
                query.strip(),
                "",
                "Use the selected skill as the "
                "primary capability. Use supporting "
                "skills only when useful.",
            ]
        )

        return "\n".join(lines)


router = SkillRouter()


def route_query(
    query: str,
) -> SkillRoute:
    return router.route(query)


def get_skill_instruction(
    query: str,
) -> str:
    return router.build_agent_instruction(
        query
    )
