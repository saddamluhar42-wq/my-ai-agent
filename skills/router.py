from dataclasses import dataclass
from typing import List

from skills.registry import (
    SkillDefinition,
    get_enabled_skills,
    get_skill,
)


@dataclass
class SkillRoute:
    primary_skill: SkillDefinition
    supporting_skills: List[SkillDefinition]


class SkillRouter:
    """
    Automatically selects the most appropriate skills
    for an incoming user request.

    Uses the central Skill Registry and lightweight
    keyword matching.
    """

    def __init__(
        self,
        skill_registry=None,
    ):
        self.registry = skill_registry

    def _get_skills(self):
        if self.registry is not None:

            if hasattr(
                self.registry,
                "enabled",
            ):
                return self.registry.enabled()

            if hasattr(
                self.registry,
                "all",
            ):
                return [
                    skill
                    for skill in self.registry.all()
                    if skill.enabled
                ]

        return get_enabled_skills()

    def _score_skill(
        self,
        query: str,
        skill: SkillDefinition,
    ) -> int:

        query_lower = query.lower().strip()

        if not query_lower:
            return 0

        score = 0

        # Exact skill-name match
        if skill.name.lower() in query_lower:
            score += 100

        # Keyword matching
        for keyword in skill.keywords:

            keyword = str(
                keyword or ""
            ).lower().strip()

            if not keyword:
                continue

            if keyword in query_lower:
                score += 10

        # Small priority contribution
        score += max(
            0,
            min(
                int(skill.priority),
                100,
            ),
        ) // 10

        return score

    def _rank_skills(
        self,
        query: str,
    ) -> List[SkillDefinition]:

        skills = self._get_skills()

        scored = []

        for skill in skills:

            score = self._score_skill(
                query,
                skill,
            )

            scored.append(
                (
                    score,
                    skill.priority,
                    skill.name,
                    skill,
                )
            )

        scored.sort(
            key=lambda item: (
                item[0],
                item[1],
                item[2],
            ),
            reverse=True,
        )

        return [
            item[3]
            for item in scored
            if item[0] > 0
        ]

    def route(
        self,
        query: str,
        max_supporting_skills: int = 3,
    ) -> SkillRoute:

        query = str(
            query or ""
        ).strip()

        general = (
            self._get_general_skill()
        )

        if not query:

            return SkillRoute(
                primary_skill=general,
                supporting_skills=[],
            )

        matches = self._rank_skills(
            query
        )

        if not matches:

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

        safe_limit = max(
            0,
            min(
                int(max_supporting_skills),
                10,
            ),
        )

        return SkillRoute(
            primary_skill=primary,
            supporting_skills=supporting[
                :safe_limit
            ],
        )

    def _get_general_skill(
        self,
    ) -> SkillDefinition:

        general = get_skill(
            "general_knowledge"
        )

        if general is not None:
            return general

        skills = self._get_skills()

        if skills:
            return skills[0]

        # Defensive fallback.
        return SkillDefinition(
            name="general_knowledge",
            description=(
                "General reasoning and "
                "question answering."
            ),
            keywords=[],
            priority=100,
            enabled=True,
        )

    def explain_route(
        self,
        query: str,
    ) -> str:

        route = self.route(
            query
        )

        lines = [
            "SKILL ROUTING",
            f"Primary: "
            f"{route.primary_skill.name}",
        ]

        if route.supporting_skills:

            lines.append(
                "Supporting:"
            )

            for skill in (
                route.supporting_skills
            ):

                lines.append(
                    f"- {skill.name}"
                )

        return "\n".join(
            lines
        )

    def build_agent_instruction(
        self,
        query: str,
    ) -> str:

        route = self.route(
            query
        )

        lines = [
            "SELECTED PRIMARY SKILL:",
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

            for skill in (
                route.supporting_skills
            ):

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
                "Use the primary skill first.",
                "Use supporting skills when they "
                "actually improve the result.",
                "Do not pretend a skill was used "
                "when it was not actually available.",
            ]
        )

        return "\n".join(
            lines
        )


router = SkillRouter()


def route_query(
    query: str,
) -> SkillRoute:

    return router.route(
        query
    )


def get_skill_instruction(
    query: str,
) -> str:

    return router.build_agent_instruction(
        query
    )
