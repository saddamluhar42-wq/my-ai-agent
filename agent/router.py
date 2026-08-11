from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentRoute:
    intent: str
    skill: str
    requires_web: bool = False
    requires_file: bool = False
    requires_image: bool = False
    requires_calculator: bool = False
    requires_memory: bool = True
    requires_planning: bool = False
    confidence: float = 1.0
    metadata: dict[str, Any] = field(
        default_factory=dict
    )


class AgentRouter:
    """
    Central intent router for My AI Agent.

    The router decides what kind of capability
    a user request needs before execution.
    """

    def route(self, query: str) -> AgentRoute:

        text = self._normalize(query)

        if not text:
            return AgentRoute(
                intent="general",
                skill="general_qa",
                confidence=1.0,
            )

        if self._is_image_generation(text):
            return AgentRoute(
                intent="image_generation",
                skill="image_generation",
                requires_image=True,
                confidence=0.95,
            )

        if self._is_file_analysis(text):
            return AgentRoute(
                intent="file_analysis",
                skill="file_analysis",
                requires_file=True,
                confidence=0.95,
            )

        if self._is_calculation(text):
            return AgentRoute(
                intent="calculation",
                skill="calculator",
                requires_calculator=True,
                requires_memory=False,
                confidence=0.92,
            )

        if self._is_web_research(text):
            return AgentRoute(
                intent="web_research",
                skill="web_search",
                requires_web=True,
                requires_planning=True,
                confidence=0.94,
            )

        if self._is_coding(text):
            return AgentRoute(
                intent="coding",
                skill="coding",
                requires_planning=True,
                confidence=0.93,
            )

        if self._is_debugging(text):
            return AgentRoute(
                intent="debugging",
                skill="debugging",
                requires_planning=True,
                confidence=0.94,
            )

        if self._is_research(text):
            return AgentRoute(
                intent="research",
                skill="research",
                requires_planning=True,
                confidence=0.88,
            )

        if self._is_translation(text):
            return AgentRoute(
                intent="translation",
                skill="translation",
                requires_memory=False,
                confidence=0.94,
            )

        if self._is_summary(text):
            return AgentRoute(
                intent="summarization",
                skill="summarization",
                confidence=0.93,
            )

        if self._is_writing(text):
            return AgentRoute(
                intent="writing",
                skill="writing",
                confidence=0.88,
            )

        if self._is_memory_request(text):
            return AgentRoute(
                intent="memory",
                skill="memory",
                requires_memory=True,
                confidence=0.96,
            )

        return AgentRoute(
            intent="general",
            skill="general_qa",
            requires_memory=True,
            confidence=0.70,
        )

    # ========================================================
    # NORMALIZATION
    # ========================================================

    @staticmethod
    def _normalize(text: str) -> str:

        return " ".join(
            str(text or "")
            .strip()
            .lower()
            .split()
        )

    # ========================================================
    # IMAGE
    # ========================================================

    @staticmethod
    def _is_image_generation(
        text: str,
    ) -> bool:

        keywords = (
            "image banao",
            "image bana",
            "photo banao",
            "picture banao",
            "tasveer banao",
            "generate image",
            "generate an image",
            "create image",
            "create an image",
            "make image",
            "make an image",
            "draw image",
            "draw a picture",
            "visualize",
            "poster banao",
            "thumbnail banao",
            "thumbnail bana",
        )

        return any(
            keyword in text
            for keyword in keywords
        )

    # ========================================================
    # FILE
    # ========================================================

    @staticmethod
    def _is_file_analysis(
        text: str,
    ) -> bool:

        keywords = (
            "pdf analyze",
            "pdf analyse",
            "pdf padho",
            "pdf padh",
            "file analyze",
            "file analyse",
            "file padho",
            "document analyze",
            "document analyse",
            "document padho",
            "uploaded file",
            "attached file",
            "attachment",
            "is file me",
            "is pdf me",
            "document me",
        )

        return any(
            keyword in text
            for keyword in keywords
        )

    # ========================================================
    # CALCULATOR
    # ========================================================

    @staticmethod
    def _is_calculation(
        text: str,
    ) -> bool:

        keywords = (
            "calculate",
            "calculation",
            "calculate karo",
            "hisab karo",
            "kitna hoga",
            "kitne honge",
            "percentage",
            "percent",
            "multiply",
            "divide",
            "plus",
            "minus",
            "sum of",
            "average",
            "average nikalo",
            "convert",
            "conversion",
        )

        return any(
            keyword in text
            for keyword in keywords
        )

    # ========================================================
    # WEB
    # ========================================================

    @staticmethod
    def _is_web_research(
        text: str,
    ) -> bool:

        keywords = (
            "latest",
            "today",
            "current",
            "right now",
            "abhi",
            "aaj",
            "recent",
            "news",
            "news batao",
            "search web",
            "web search",
            "internet par",
            "online check",
            "check online",
            "real time",
            "real-time",
            "live information",
            "current price",
            "current weather",
            "weather",
            "mausam",
            "forecast",
            "weather today",
            "latest update",
        )

        return any(
            keyword in text
            for keyword in keywords
        )

    # ========================================================
    # CODING
    # ========================================================

    @staticmethod
    def _is_coding(
        text: str,
    ) -> bool:

        keywords = (
            "code",
            "coding",
            "python",
            "javascript",
            "typescript",
            "java",
            "kotlin",
            "android",
            "streamlit",
            "customtkinter",
            "sql",
            "postgresql",
            "sqlite",
            "api",
            "program banao",
            "app banao",
            "software banao",
            "function banao",
            "script banao",
            "complete code",
            "full code",
        )

        return any(
            keyword in text
            for keyword in keywords
        )

    # ========================================================
    # DEBUGGING
    # ========================================================

    @staticmethod
    def _is_debugging(
        text: str,
    ) -> bool:

        keywords = (
            "error",
            "error aa raha",
            "error aa rha",
            "error solve",
            "fix this",
            "fix karo",
            "debug",
            "debugging",
            "traceback",
            "exception",
            "importerror",
            "typeerror",
            "syntaxerror",
            "indentationerror",
            "not working",
            "kaam nahi kar",
            "work nahi kar",
            "crash",
            "failed",
            "failure",
            "bug",
        )

        return any(
            keyword in text
            for keyword in keywords
        )

    # ========================================================
    # RESEARCH
    # ========================================================

    @staticmethod
    def _is_research(
        text: str,
    ) -> bool:

        keywords = (
            "research",
            "deep research",
            "detail me research",
            "compare",
            "comparison",
            "pros and cons",
            "advantages and disadvantages",
            "in detail",
            "detail me batao",
            "thoroughly",
            "investigate",
            "study this",
            "analyze deeply",
        )

        return any(
            keyword in text
            for keyword in keywords
        )

    # ========================================================
    # TRANSLATION
    # ========================================================

    @staticmethod
    def _is_translation(
        text: str,
    ) -> bool:

        keywords = (
            "translate",
            "translation",
            "translate karo",
            "hindi me translate",
            "english me translate",
            "gujarati me translate",
            "urdu me translate",
            "meaning batao",
            "ka matlab kya hai",
        )

        return any(
            keyword in text
            for keyword in keywords
        )

    # ========================================================
    # SUMMARY
    # ========================================================

    @staticmethod
    def _is_summary(
        text: str,
    ) -> bool:

        keywords = (
            "summarize",
            "summary",
            "short me batao",
            "short summary",
            "summarise",
            "main points",
            "key points",
            "important points",
            "brief me",
            "short me",
        )

        return any(
            keyword in text
            for keyword in keywords
        )

    # ========================================================
    # WRITING
    # ========================================================

    @staticmethod
    def _is_writing(
        text: str,
    ) -> bool:

        keywords = (
            "write",
            "likho",
            "likh do",
            "draft",
            "script likho",
            "email likho",
            "letter likho",
            "description likho",
            "article likho",
            "story likho",
            "caption likho",
            "title likho",
        )

        return any(
            keyword in text
            for keyword in keywords
        )

    # ========================================================
    # MEMORY
    # ========================================================

    @staticmethod
    def _is_memory_request(
        text: str,
    ) -> bool:

        keywords = (
            "remember this",
            "yaad rakho",
            "yaad rakhna",
            "remember karo",
            "save this",
            "save karo",
            "meri preference",
            "my preference",
            "what did i say",
            "maine kya kaha",
            "pichli baar",
            "last time",
            "previous conversation",
            "purani chat",
            "meri memory",
        )

        return any(
            keyword in text
            for keyword in keywords
        )


# ============================================================
# SINGLETON ROUTER
# ============================================================

_router = AgentRouter()


def route_request(
    query: str,
) -> AgentRoute:

    return _router.route(
        query
    )


def get_route_dict(
    query: str,
) -> dict[str, Any]:

    route = route_request(
        query
    )

    return {
        "intent": route.intent,
        "skill": route.skill,
        "requires_web": route.requires_web,
        "requires_file": route.requires_file,
        "requires_image": route.requires_image,
        "requires_calculator": (
            route.requires_calculator
        ),
        "requires_memory": (
            route.requires_memory
        ),
        "requires_planning": (
            route.requires_planning
        ),
        "confidence": route.confidence,
        "metadata": route.metadata,
    }
