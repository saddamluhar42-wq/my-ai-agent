"""Cross-domain knowledge graph reasoning primitives.

The module is intentionally bounded: it derives only paths already present in the
stored graph and labels every result as an inference rather than a verified fact.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Tuple


@dataclass(frozen=True)
class GraphEdge:
    source: str
    relation: str
    target: str
    confidence: float = 1.0
    domain: str = "general"


@dataclass
class ReasoningPath:
    nodes: List[str]
    relations: List[str]
    confidence: float
    domains: List[str]
    conclusion_type: str = "derived_inference"


class CrossDomainReasoner:
    """Find short, explainable paths connecting concepts across domains."""

    def __init__(self, max_hops: int = 3):
        self.max_hops = max(1, min(5, max_hops))

    def _adjacency(self, edges: Iterable[GraphEdge]) -> Dict[str, List[GraphEdge]]:
        graph: Dict[str, List[GraphEdge]] = {}
        for edge in edges:
            graph.setdefault(edge.source, []).append(edge)
        return graph

    def connect(self, source: str, target: str, edges: Iterable[GraphEdge], limit: int = 5) -> List[ReasoningPath]:
        graph = self._adjacency(edges)
        source, target = source.strip(), target.strip()
        if not source or not target:
            return []
        queue: List[Tuple[str, List[str], List[str], float, List[str]]] = [(source, [source], [], 1.0, [])]
        results: List[ReasoningPath] = []
        visited = {(source, 0)}
        while queue and len(results) < max(1, limit):
            node, nodes, relations, confidence, domains = queue.pop(0)
            if node == target and len(nodes) > 1:
                results.append(ReasoningPath(nodes, relations, confidence, domains))
                continue
            if len(relations) >= self.max_hops:
                continue
            for edge in graph.get(node, []):
                if edge.target in nodes:
                    continue
                depth = len(relations) + 1
                state = (edge.target, depth)
                if state in visited:
                    continue
                visited.add(state)
                queue.append((edge.target, nodes + [edge.target], relations + [edge.relation],
                              confidence * max(0.0, min(1.0, edge.confidence)), domains + [edge.domain]))
        return sorted(results, key=lambda p: p.confidence, reverse=True)

    def bridge(self, source: str, target: str, edges: Iterable[GraphEdge]) -> Dict[str, Any]:
        paths = self.connect(source, target, edges)
        return {
            "source": source,
            "target": target,
            "paths": [
                {
                    "nodes": p.nodes,
                    "relations": p.relations,
                    "confidence": round(p.confidence, 4),
                    "domains": p.domains,
                    "type": p.conclusion_type,
                }
                for p in paths
            ],
            "cross_domain_connection_found": bool(paths),
            "warning": "Connections are graph-derived inferences; verify underlying evidence before treating them as facts.",
        }
