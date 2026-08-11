from typing import Any, Dict, List, Optional

from agent.knowledge import (
    extract_learning_candidates,
    save_knowledge,
)


class EvolutionEngine:
    """
    Self-evolution controller.

    The agent does not blindly memorize every message.
    It evaluates candidate knowledge and stores only
    information that is useful for future interactions.
    """

    def __init__(
        self,
        enabled: bool = True,
        minimum_confidence: float = 0.70,
    ):
        self.enabled = enabled
        self.minimum_confidence = (
            minimum_confidence
        )

    def learn_from_interaction(
        self,
        user_id: Optional[int],
        query: str,
        answer: str,
        source: str = "conversation",
    ) -> List[Dict[str, Any]]:

        if not self.enabled:
            return []

        candidates = (
            extract_learning_candidates(
                query=query,
                answer=answer,
            )
        )

        learned = []

        for candidate in candidates:

            confidence = float(
                candidate.get(
                    "confidence",
                    0.0,
                )
            )

            if confidence < self.minimum_confidence:
                continue

            key = str(
                candidate.get(
                    "key",
                    "",
                )
            ).strip()

            value = str(
                candidate.get(
                    "value",
                    "",
                )
            ).strip()

            category = str(
                candidate.get(
                    "category",
                    "general",
                )
            ).strip()

            if not key or not value:
                continue

            knowledge_id = save_knowledge(
                user_id=user_id,
                key=key,
                value=value,
                category=category,
                source=source,
                confidence=confidence,
            )

            if knowledge_id:

                learned.append(
                    {
                        "id": knowledge_id,
                        "key": key,
                        "category": category,
                        "confidence": confidence,
                    }
                )

        return learned

    def evaluate_candidate(
        self,
        candidate: Dict[str, Any],
    ) -> bool:

        if not candidate:
            return False

        value = str(
            candidate.get(
                "value",
                "",
            )
        ).strip()

        key = str(
            candidate.get(
                "key",
                "",
            )
        ).strip()

        confidence = float(
            candidate.get(
                "confidence",
                0.0,
            )
        )

        if not key or not value:
            return False

        if confidence < self.minimum_confidence:
            return False

        return True

    def evolve(
        self,
        user_id: Optional[int],
        query: str,
        answer: str,
    ) -> Dict[str, Any]:

        if not self.enabled:

            return {
                "enabled": False,
                "learned": [],
                "count": 0,
            }

        learned = (
            self.learn_from_interaction(
                user_id=user_id,
                query=query,
                answer=answer,
            )
        )

        return {
            "enabled": True,
            "learned": learned,
            "count": len(learned),
        }


evolution_engine = EvolutionEngine()


def evolve_from_interaction(
    user_id: Optional[int],
    query: str,
    answer: str,
) -> Dict[str, Any]:

    return evolution_engine.evolve(
        user_id=user_id,
        query=query,
        answer=answer,
    )


def set_evolution_enabled(
    enabled: bool,
):

    evolution_engine.enabled = bool(
        enabled
    )


def get_evolution_status():

    return {
        "enabled": evolution_engine.enabled,
        "minimum_confidence": (
            evolution_engine.minimum_confidence
        ),
    }
