"""Advanced research orchestration and source verification primitives."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import urlparse


@dataclass
class ResearchSource:
    url: str
    title: str = ""
    content: str = ""
    source_type: str = "web"
    published_at: Optional[str] = None
    retrieved_at: Optional[str] = None
    authority: float = 0.5
    relevance: float = 0.5
    freshness: float = 0.5
    claims: List[str] = field(default_factory=list)


@dataclass
class VerifiedClaim:
    claim: str
    supporting_sources: List[str]
    contradicting_sources: List[str]
    confidence: float
    status: str


class SourceVerifier:
    """Score evidence quality and identify corroboration/conflicts.

    This layer does not declare a claim true solely from source count; independent
    evidence and source quality remain separate signals.
    """

    TRUSTED_TYPES = {"official", "primary", "academic", "government", "documentation"}

    @staticmethod
    def _clamp(value: float) -> float:
        return max(0.0, min(1.0, float(value)))

    def score_source(self, source: ResearchSource) -> float:
        return self._clamp(
            0.40 * source.authority +
            0.30 * source.relevance +
            0.20 * source.freshness +
            0.10 * (1.0 if source.source_type.lower() in self.TRUSTED_TYPES else 0.5)
        )

    def rank_sources(self, sources: Iterable[ResearchSource]) -> List[ResearchSource]:
        return sorted(list(sources), key=self.score_source, reverse=True)

    def verify_claim(self, claim: str, supporting: Iterable[ResearchSource], contradicting: Iterable[ResearchSource] = ()) -> VerifiedClaim:
        supports = list(supporting)
        conflicts = list(contradicting)
        support_score = max((self.score_source(s) for s in supports), default=0.0)
        independent = len({self._domain(s.url) for s in supports if self._domain(s.url)})
        corroboration = min(1.0, independent / 3.0)
        conflict_penalty = min(0.45, 0.15 * len(conflicts))
        confidence = self._clamp(0.65 * support_score + 0.35 * corroboration - conflict_penalty)
        if conflicts:
            status = "conflicted"
        elif confidence >= 0.75:
            status = "strongly_supported"
        elif confidence >= 0.45:
            status = "partially_supported"
        else:
            status = "insufficient_evidence"
        return VerifiedClaim(claim, [s.url for s in supports], [s.url for s in conflicts], confidence, status)

    @staticmethod
    def _domain(url: str) -> str:
        try:
            return urlparse(url).netloc.lower().removeprefix("www.")
        except Exception:
            return ""


class ResearchOrchestrator:
    """Bounded research plan; actual web fetching is injected by the host application."""

    def __init__(self, max_sources: int = 12, max_claims: int = 30):
        self.max_sources = max(1, min(50, max_sources))
        self.max_claims = max(1, min(100, max_claims))
        self.verifier = SourceVerifier()

    def prepare(self, query: str, sources: Iterable[ResearchSource]) -> Dict[str, Any]:
        ranked = self.verifier.rank_sources(sources)[: self.max_sources]
        claims: Dict[str, List[ResearchSource]] = {}
        for source in ranked:
            for claim in source.claims[: self.max_claims]:
                claims.setdefault(claim.strip(), []).append(source)
        verified = [self.verifier.verify_claim(claim, evidence) for claim, evidence in list(claims.items())[: self.max_claims] if claim]
        return {
            "query": query,
            "sources": [s.url for s in ranked],
            "claims": [v.__dict__ for v in verified],
            "source_count": len(ranked),
            "claim_count": len(verified),
        }
