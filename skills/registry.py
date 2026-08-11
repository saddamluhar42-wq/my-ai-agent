from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


@dataclass
class Skill:
    name: str
    description: str
    keywords: List[str] = field(default_factory=list)
    handler: Optional[Callable] = None
    priority: int = 0
    enabled: bool = True

    def matches(self, query: str) -> bool:
        if not self.enabled:
            return False

        query = (query or "").lower().strip()

        if not query:
            return False

        return any(
            keyword.lower() in query
            for keyword in self.keywords
        )


class SkillRegistry:
    """
    Central registry for all AI Agent skills.

    Responsibilities:
    - Register skills
    - Enable/disable skills
    - Find matching skills
    - Rank skills
    - Provide skill information to the agent
    """

    def __init__(self):
        self._skills: Dict[str, Skill] = {}

    def register(
        self,
        name: str,
        description: str,
        keywords: Optional[List[str]] = None,
        handler: Optional[Callable] = None,
        priority: int = 0,
    ) -> Skill:
        skill = Skill(
            name=name,
            description=description,
            keywords=keywords or [],
            handler=handler,
            priority=priority,
            enabled=True,
        )

        self._skills[name] = skill

        return skill

    def unregister(self, name: str) -> bool:
        if name not in self._skills:
            return False

        del self._skills[name]
        return True

    def enable(self, name: str) -> bool:
        skill = self._skills.get(name)

        if not skill:
            return False

        skill.enabled = True
        return True

    def disable(self, name: str) -> bool:
        skill = self._skills.get(name)

        if not skill:
            return False

        skill.enabled = False
        return True

    def get(self, name: str) -> Optional[Skill]:
        return self._skills.get(name)

    def all(self) -> List[Skill]:
        return list(self._skills.values())

    def enabled(self) -> List[Skill]:
        return [
            skill
            for skill in self._skills.values()
            if skill.enabled
        ]

    def find_matches(
        self,
        query: str,
        limit: int = 5,
    ) -> List[Skill]:
        matches = []

        for skill in self.enabled():
            if skill.matches(query):
                matches.append(skill)

        matches.sort(
            key=lambda skill: skill.priority,
            reverse=True,
        )

        return matches[:limit]

    def get_skill_names(self) -> List[str]:
        return [
            skill.name
            for skill in self.enabled()
        ]

    def build_skill_context(self) -> str:
        skills = self.enabled()

        if not skills:
            return "No specialized skills are currently available."

        lines = [
            "AVAILABLE AGENT SKILLS:"
        ]

        for skill in skills:
            lines.append(
                f"- {skill.name}: "
                f"{skill.description}"
            )

        return "\n".join(lines)


registry = SkillRegistry()


def register_default_skills():
    """
    Register the initial built-in skill categories.

    Actual implementations will be connected
    in later project files.
    """

    if registry.all():
        return registry

    registry.register(
        name="general_knowledge",
        description=(
            "Answer general questions, explanations, "
            "reasoning and everyday knowledge."
        ),
        keywords=[
            "what",
            "why",
            "how",
            "explain",
            "meaning",
            "difference",
            "who",
            "when",
            "where",
        ],
        priority=10,
    )

    registry.register(
        name="web_research",
        description=(
            "Find and reason about current or "
            "time-sensitive information from the web."
        ),
        keywords=[
            "latest",
            "today",
            "current",
            "news",
            "recent",
            "search",
            "online",
            "internet",
            "price",
            "weather",
        ],
        priority=30,
    )

    registry.register(
        name="coding",
        description=(
            "Write, explain, debug, review and "
            "improve programming code."
        ),
        keywords=[
            "code",
            "python",
            "javascript",
            "typescript",
            "java",
            "kotlin",
            "html",
            "css",
            "sql",
            "programming",
            "bug",
            "error",
            "debug",
        ],
        priority=40,
    )

    registry.register(
        name="file_analysis",
        description=(
            "Analyze uploaded documents, PDFs, "
            "text files and other supported files."
        ),
        keywords=[
            "file",
            "pdf",
            "document",
            "uploaded",
            "attachment",
            "read",
            "analyze",
            "summarize",
        ],
        priority=35,
    )

    registry.register(
        name="image_understanding",
        description=(
            "Understand and analyze images supplied "
            "by the user."
        ),
        keywords=[
            "image",
            "photo",
            "picture",
            "screenshot",
            "visual",
            "image analysis",
        ],
        priority=35,
    )

    registry.register(
        name="writing",
        description=(
            "Create, rewrite, improve and structure "
            "written content."
        ),
        keywords=[
            "write",
            "rewrite",
            "draft",
            "article",
            "script",
            "email",
            "story",
            "description",
            "title",
        ],
        priority=20,
    )

    registry.register(
        name="memory",
        description=(
            "Use relevant conversation history and "
            "stored knowledge to maintain context."
        ),
        keywords=[
            "remember",
            "previous",
            "earlier",
            "last time",
            "before",
            "memory",
            "history",
        ],
        priority=25,
    )

    registry.register(
        name="self_evolution",
        description=(
            "Learn from feedback, identify missing "
            "capabilities and improve the agent's "
            "knowledge and skill configuration."
        ),
        keywords=[
            "learn",
            "improve",
            "evolve",
            "feedback",
            "mistake",
            "better",
            "teach",
        ],
        priority=50,
    )

    return registry


register_default_skills()
