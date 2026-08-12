"""Offline integration smoke test for the Ultra Legend foundation."""
from __future__ import annotations

import tempfile
from pathlib import Path

from agent.model_ensemble import ModelEnsemble, ModelProfile
from agent.self_evaluation import RecoveryController, SelfEvaluator
from agent.tool_orchestrator import PluginOrchestrator, ToolRegistry, ToolSpec
from core.ultra_legend import UltraLegend
from evaluation.continuous_eval import ContinuousEvaluator, EvalCase, RegressionGate
from evaluation.stress_suite import StressCase, StressSuite
from knowledge.cross_domain import CrossDomainReasoner, GraphEdge
from knowledge.multimodal_intelligence import MultimodalIntelligence
from memory.intelligence import MemoryIntelligence
from memory.long_term import LongTermMemory, MemoryRecord
from ops.production_hardening import OperationBudget, ProductionHealth
from research.source_verification import ResearchSource, SourceVerifier


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db = str(Path(tmp) / "memory.sqlite3")
        memory = LongTermMemory(db)
        assert memory.remember(MemoryRecord("Python testing workflow", category="engineering", importance=0.9))
        assert memory.count() == 1
        assert memory.search("Python testing")
        intelligence = MemoryIntelligence(db)
        assert intelligence.rank("Python testing", limit=1)[0].action == "retrieve"

    graph = [
        GraphEdge("python", "used_for", "automation", 0.9, "software"),
        GraphEdge("automation", "supports", "research", 0.8, "research"),
    ]
    assert CrossDomainReasoner().connect("python", "research", graph)

    multimodal = MultimodalIntelligence()
    evidence = multimodal.normalize([
        {"modality": "text", "content": "entity value is A", "confidence": 0.9, "attributes": {"entity": "x", "value": "A"}},
        {"modality": "image", "content": "entity value is A", "confidence": 0.8, "attributes": {"entity": "x", "value": "A"}},
    ])
    assert multimodal.fuse(evidence).confidence > 0

    ensemble = ModelEnsemble([ModelProfile("test-model", ["research"], reliability=0.95)])
    result = ensemble.run("research", {"test-model": lambda _: "answer"}, ["research"])
    assert result.selected == "answer"

    registry = ToolRegistry()
    registry.register(ToolSpec("calculator", "safe calculation", ["calculate"]))
    tools = PluginOrchestrator(registry)
    assert tools.plan("calculate", ["calculate"])

    verifier = SourceVerifier()
    source = ResearchSource("https://example.org", source_type="academic", authority=0.9, relevance=0.9, freshness=0.9)
    assert verifier.verify_claim("test", [source]).status == "strongly_supported"

    evaluator = SelfEvaluator()
    recovery = RecoveryController(max_retries=1)
    value, evaluation, attempts = recovery.run(lambda: "ok", evaluator, expected=lambda x: x == "ok")
    assert value == "ok" and evaluation.status.value == "pass" and attempts == 1

    benchmark = ContinuousEvaluator().run(lambda task: task.upper(), [EvalCase("1", "ok", "OK")])
    assert benchmark.pass_rate == 1.0
    assert RegressionGate().approve(benchmark)["approved"]

    budget = OperationBudget()
    budget.consume_tool()
    assert ProductionHealth(db).check().healthy

    core = UltraLegend()
    assert core.health_snapshot()["status"] == "ready"
    assert core.run("ping", lambda _: "pong").answer == "pong"

    stress = StressSuite().run([StressCase("core", lambda: core.run("ping", lambda _: "pong"))])
    assert StressSuite.summary(stress)["pass_rate"] == 1.0
    print("ULTRA_LEGEND_INTEGRATION_SMOKE: PASS")


if __name__ == "__main__":
    main()
