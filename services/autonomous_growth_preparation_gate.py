"""Autonomous Growth Preparation Gate for AGOS."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.growth_signal_correlation_engine import GrowthSignalCorrelationEngine
from services.heat_detection_engine import HeatDetectionEngine
from services.long_term_strategy_memory import LongTermStrategyMemory
from services.personality_evolution_gate import PersonalityEvolutionGate
from services.real_growth_validation_engine import RealGrowthValidationEngine
from services.runtime_engine import RuntimeEngine
from services.runtime_persistence import utc_now_iso
from services.runtime_priority_engine import RuntimePriorityEngine
from services.runtime_strategy_simulation import RuntimeStrategySimulation
from services.trend_clustering_engine import TrendClusteringEngine


class AutonomousGrowthPreparationGate:
    """Validate whether AGOS is ready for the semi-autonomous runtime stage."""

    def __init__(self, root: str | Path = "runtime/autonomous_growth_preparation_gate") -> None:
        self.root = Path(root)
        self.report_path = self.root / "AUTONOMOUS_GROWTH_PREPARATION_REPORT.json"
        self.review_path = self.root / "RUNTIME_INTELLIGENCE_REVIEW.json"
        self.checks_path = self.root / "autonomous_growth_preparation_checks.json"

    def evaluate(self) -> dict[str, Any]:
        runtime_state = RuntimeEngine().current_state()
        personality = PersonalityEvolutionGate().state()
        trends = TrendClusteringEngine().state()
        heat = HeatDetectionEngine().state()
        real_ops = RealGrowthValidationEngine().state()
        strategy_memory = LongTermStrategyMemory().state()
        priority = RuntimePriorityEngine().state()
        correlation = GrowthSignalCorrelationEngine().state()
        simulation = RuntimeStrategySimulation().state()

        checks = [
            self._check(
                "Runtime Intelligence",
                bool(runtime_state.get("pipeline")) and bool(runtime_state.get("current_stage")),
                "Runtime state machine, current stage, and pipeline are available.",
            ),
            self._check(
                "Personality Intelligence",
                personality.get("status") == "passed",
                "Personality Evolution Gate passed with stable operating personality.",
            ),
            self._check(
                "Scout Intelligence",
                bool(trends.get("trendClusters")) and bool(heat.get("opportunityRanking")),
                "Scout produced trend clusters, heat signals, and opportunity ranking.",
            ),
            self._check(
                "Real Ops Intelligence",
                real_ops.get("status") == "passed",
                "Real Operations loop passed local validation.",
            ),
            self._check(
                "Strategy Intelligence",
                self._strategy_ready(strategy_memory, priority, correlation, simulation),
                "Long-term memory, priority evolution, signal correlation, and strategy simulation are active.",
            ),
        ]
        passed = all(item["status"] == "passed" for item in checks)
        review = {
            "review_id": "AUTONOMOUS_PREP_RUNTIME_INTELLIGENCE_REVIEW",
            "created_at": utc_now_iso(),
            "runtime_intelligence": self._review_item("runtime", checks[0], runtime_state.get("current_stage", "unknown")),
            "personality_intelligence": self._review_item("personality", checks[1], personality.get("personalityEvolutionSummary", "")),
            "scout_intelligence": self._review_item("scout", checks[2], heat.get("heatSummary", {}).get("top_opportunity", "none")),
            "real_ops_intelligence": self._review_item("real_ops", checks[3], real_ops.get("realGrowthValidationSummary", {}).get("growth_intelligence", "unknown")),
            "strategy_intelligence": self._review_item("strategy", checks[4], simulation.get("simulationSummary", {}).get("best_scenario", "none")),
            "next_stage": "Semi-Autonomous Runtime Stage" if passed else "Continue Autonomous Growth Preparation",
            "human_gate_required": True,
            "safety_boundary": "No autonomous posting, replying, account creation, login automation, or platform API execution is enabled.",
        }
        report = {
            "report_id": "AUTONOMOUS_GROWTH_PREPARATION_REPORT",
            "created_at": utc_now_iso(),
            "status": "passed" if passed else "needs_human_review",
            "phase": "AUTONOMOUS_GROWTH_PREPARATION",
            "checks": checks,
            "autonomousGrowthPreparationCapability": {
                "ready_for_semi_autonomous_runtime": passed,
                "human_gate_required": True,
                "runtime_intelligence": checks[0]["status"],
                "personality_intelligence": checks[1]["status"],
                "scout_intelligence": checks[2]["status"],
                "real_ops_intelligence": checks[3]["status"],
                "strategy_intelligence": checks[4]["status"],
            },
            "autonomousGrowthPreparationSummary": {
                "phase_completion": "Autonomous Growth Preparation Phase completed" if passed else "Autonomous Growth Preparation Phase needs more evidence",
                "next_stage": review["next_stage"],
                "gate_decision": "pass_to_semi_autonomous_runtime" if passed else "hold_for_review",
                "best_strategy_simulation": simulation.get("simulationSummary", {}).get("best_scenario", "none"),
                "top_priority": priority.get("prioritySummary", {}).get("top_platform", "none"),
                "strongest_growth_signal": correlation.get("correlationSummary", {}).get("strongest_content_signal", "none"),
            },
            "runtimeIntelligenceReview": review,
        }
        self.persist(report)
        return report

    def state(self) -> dict[str, Any]:
        if self.report_path.exists():
            return json.loads(self.report_path.read_text(encoding="utf-8"))
        return self.evaluate()

    def persist(self, report: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.review_path.write_text(
            json.dumps(report["runtimeIntelligenceReview"], ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        self.checks_path.write_text(json.dumps(report["checks"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    @staticmethod
    def _strategy_ready(
        memory: dict[str, Any],
        priority: dict[str, Any],
        correlation: dict[str, Any],
        simulation: dict[str, Any],
    ) -> bool:
        return bool(
            memory.get("longTermEffectiveStrategies")
            and priority.get("runtimePriorityFeed")
            and correlation.get("growthSignalCorrelationFeed")
            and simulation.get("strategySimulationScenarios")
            and simulation.get("simulationSummary", {}).get("can_predict_strategy_consequence")
        )

    @staticmethod
    def _check(name: str, passed: bool, evidence: str) -> dict[str, str]:
        return {
            "name": name,
            "status": "passed" if passed else "needs_human_review",
            "evidence": evidence if passed else f"Missing or unstable: {evidence}",
        }

    @staticmethod
    def _review_item(kind: str, check: dict[str, str], signal: str) -> dict[str, str]:
        return {
            "kind": kind,
            "status": check["status"],
            "signal": signal,
            "evidence": check["evidence"],
        }


if __name__ == "__main__":
    result = AutonomousGrowthPreparationGate().evaluate()
    print(
        json.dumps(
            {
                "status": result["status"],
                "next_stage": result["autonomousGrowthPreparationSummary"]["next_stage"],
            },
            indent=2,
        )
    )
