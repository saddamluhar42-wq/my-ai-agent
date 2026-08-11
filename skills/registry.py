from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(frozen=True)
class SkillDefinition:
    name: str
    description: str
    keywords: List[str] = field(
        default_factory=list
    )
    priority: int = 50
    enabled: bool = True


class SkillRegistry:

    def __init__(self):

        self._skills: Dict[
            str,
            SkillDefinition,
        ] = {}

    def register(
        self,
        skill: SkillDefinition,
    ):

        if not skill.name:
            raise ValueError(
                "Skill name is required."
            )

        self._skills[
            skill.name
        ] = skill

    def get(
        self,
        name: str,
    ) -> Optional[SkillDefinition]:

        return self._skills.get(
            name
        )

    def all(
        self,
    ) -> List[SkillDefinition]:

        return list(
            self._skills.values()
        )

    def enabled(
        self,
    ) -> List[SkillDefinition]:

        return [
            skill
            for skill in self._skills.values()
            if skill.enabled
        ]

    def names(
        self,
    ) -> List[str]:

        return sorted(
            self._skills.keys()
        )

    def disable(
        self,
        name: str,
    ):

        skill = self.get(name)

        if skill is None:
            return False

        self._skills[
            name
        ] = SkillDefinition(
            name=skill.name,
            description=skill.description,
            keywords=skill.keywords,
            priority=skill.priority,
            enabled=False,
        )

        return True

    def enable(
        self,
        name: str,
    ):

        skill = self.get(name)

        if skill is None:
            return False

        self._skills[
            name
        ] = SkillDefinition(
            name=skill.name,
            description=skill.description,
            keywords=skill.keywords,
            priority=skill.priority,
            enabled=True,
        )

        return True


registry = SkillRegistry()


# ============================================================
# CORE SKILLS
# ============================================================

registry.register(
    SkillDefinition(
        name="general_knowledge",
        description=(
            "General reasoning, explanations, "
            "questions and answers."
        ),
        keywords=[
            "what",
            "why",
            "how",
            "explain",
            "meaning",
            "difference",
            "help",
        ],
        priority=100,
    )
)


registry.register(
    SkillDefinition(
        name="web_research",
        description=(
            "Research current or external information "
            "from the web."
        ),
        keywords=[
            "latest",
            "today",
            "current",
            "news",
            "search",
            "research",
            "online",
            "website",
        ],
        priority=95,
    )
)


registry.register(
    SkillDefinition(
        name="coding",
        description=(
            "Programming, debugging, architecture, "
            "scripts and software development."
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
            "api",
            "bug",
            "error",
            "debug",
            "program",
        ],
        priority=95,
    )
)


registry.register(
    SkillDefinition(
        name="file_analysis",
        description=(
            "Analyze uploaded documents, files, "
            "PDFs and structured data."
        ),
        keywords=[
            "file",
            "pdf",
            "document",
            "csv",
            "json",
            "docx",
            "upload",
            "attachment",
        ],
        priority=90,
    )
)


registry.register(
    SkillDefinition(
        name="image_understanding",
        description=(
            "Understand and analyze images "
            "provided by the user."
        ),
        keywords=[
            "image",
            "photo",
            "picture",
            "screenshot",
            "visual",
            "look",
            "shown",
        ],
        priority=85,
    )
)


registry.register(
    SkillDefinition(
        name="image_generation",
        description=(
            "Generate images from natural-language "
            "descriptions."
        ),
        keywords=[
            "generate image",
            "create image",
            "make image",
            "image banao",
            "photo banao",
            "picture banao",
            "draw",
            "illustration",
        ],
        priority=90,
    )
)


registry.register(
    SkillDefinition(
        name="memory",
        description=(
            "Use relevant conversation memory "
            "and persistent knowledge."
        ),
        keywords=[
            "remember",
            "previous",
            "earlier",
            "before",
            "memory",
            "saved",
        ],
        priority=80,
    )
)


registry.register(
    SkillDefinition(
        name="self_evolution",
        description=(
            "Evaluate useful information from "
            "interactions for future learning."
        ),
        keywords=[
            "learn",
            "learning",
            "evolve",
            "improve",
            "remember this",
            "save this",
        ],
        priority=75,
    )
)


# ============================================================
# PUBLIC HELPERS
# ============================================================

def get_skill(
    name: str,
) -> Optional[SkillDefinition]:

    return registry.get(name)


def get_all_skills() -> List[SkillDefinition]:

    return registry.all()


def get_enabled_skills() -> List[SkillDefinition]:

    return registry.enabled()


def get_skill_names() -> List[str]:

    return registry.names()


def register_skill(
    name: str,
    description: str,
    keywords: Optional[List[str]] = None,
    priority: int = 50,
):

    skill = SkillDefinition(
        name=name,
        description=description,
        keywords=keywords or [],
        priority=priority,
        enabled=True,
    )

    registry.register(skill)


def enable_skill(
    name: str,
) -> bool:

    return registry.enable(name)


def disable_skill(
    name: str,
) -> bool:

    return registry.disable(name)
