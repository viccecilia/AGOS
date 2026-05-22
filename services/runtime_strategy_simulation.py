"""Runtime strategy simulation for AGOS autonomous growth preparation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.growth_signal_correlation_engine import GrowthSignalCorrelationEngine
from services.long_term_strategy_memory import LongTermStrategyMemory
from services.runtime_persistence import utc_now_iso
from services.runtime_priority_engine import RuntimePriorityEngine


class RuntimeStrategySimulation:
    """Simulate likely outcomes before AGOS changes operating strategy."""

    def __init__(self, root: str | Path = "runtime/strategy_simulation") -> None:
        self.root = Path(root)
        self.report_path = self.root / "STRATEGY_SIMULATION_REPORT.json"
        self.scenarios_path = self.root / "strategy_simulation_scenarios.json"
        self.feed_path = self.root / "strategy_simulation_feed.json"

    def simulate(self) -> dict[str, Any]:
        priority = RuntimePriorityEngine().state()
        correlation = GrowthSignalCorrelationEngine().state()
        memory = LongTermStrategyMemory().state()
        context = self._context(priority, correlation, memory)
        scenarios = [
            self._simulate_increase_reddit(context),
            self._simulate_reduce_tiktok(context),
            self._simulate_strengthen_korea(context),
            self._simulate_stop_failed_strategy(context),
        ]
        report = {
            "report_id": "STRATEGY_SIMULATION_REPORT",
            "created_at": utc_now_iso(),
            "status": "simulating_strategy_outcomes",
            "scope": "local_strategy_simulation_only",
            "simulationContext": context,
            "strategySimulationScenarios": scenarios,
            "strategySimulationFeed": self._feed(scenarios),
            "simulationSummary": {
                "best_scenario": self._best_scenario(scenarios),
                "highest_risk_scenario": self._highest_risk(scenarios),
                "can_predict_strategy_consequence": bool(scenarios),
                "requires_human_review": True,
            },
            "safetyBoundary": "Simulation only informs local planning and human-reviewed strategy candidates.",
        }
        self.persist(report)
        return report

    def state(self) -> dict[str, Any]:
        if self.report_path.exists():
            return json.loads(self.report_path.read_text(encoding="utf-8"))
        return self.simulate()

    def persist(self, report: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.scenarios_path.write_text(
            json.dumps(report["strategySimulationScenarios"], ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        self.feed_path.write_text(
            json.dumps(report["strategySimulationFeed"], ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    @staticmethod
    def _context(priority: dict[str, Any], correlation: dict[str, Any], memory: dict[str, Any]) -> dict[str, Any]:
        summary = correlation.get("correlationSummary", {})
        priority_summary = priority.get("prioritySummary", {})
        horizon = memory.get("strategyHorizonClassification", {})
        return {
            "top_platform": priority_summary.get("top_platform", "none"),
            "top_question": priority_summary.get("top_question", "none"),
            "top_content": priority_summary.get("top_content", "none"),
            "strongest_content_signal": summary.get("strongest_content_signal", "none"),
            "strongest_platform_signal": summary.get("strongest_platform_signal", "none"),
            "strongest_hook_signal": summary.get("strongest_hook_signal", "none"),
            "strongest_personality_signal": summary.get("strongest_personality_signal", "none"),
            "primary_long_term_direction": horizon.get("primary_long_term_direction", "none"),
            "avoid_overweighting": horizon.get("avoid_overweighting", []),
        }

    @staticmethod
    def _simulate_increase_reddit(context: dict[str, Any]) -> dict[str, Any]:
        base = 0.68
        if str(context.get("top_platform", "")).lower() == "reddit":
            base += 0.14
        if str(context.get("strongest_platform_signal", "")).lower() == "reddit":
            base += 0.12
        return RuntimeStrategySimulation._scenario(
            "SIM-001",
            "increase_reddit_content",
            "If AGOS increases Reddit content with durable guide-style answers.",
            base,
            0.24,
            "Likely improves trust and reply quality because Reddit is both priority leader and strongest platform signal.",
            "Increase human-reviewed Reddit answers around the strongest question focus.",
        )

    @staticmethod
    def _simulate_reduce_tiktok(context: dict[str, Any]) -> dict[str, Any]:
        risk = 0.2 if "tiktok" in context.get("avoid_overweighting", []) else 0.35
        score = 0.58 if "tiktok" in context.get("avoid_overweighting", []) else 0.42
        return RuntimeStrategySimulation._scenario(
            "SIM-002",
            "reduce_tiktok_weight",
            "If AGOS reduces TikTok weight and keeps it as experiment only.",
            score,
            risk,
            "Likely reduces short-term traffic exposure but protects long-term trust from over-weighting spike-based tactics.",
            "Keep TikTok hooks in test mode and require human review before promotion.",
        )

    @staticmethod
    def _simulate_strengthen_korea(context: dict[str, Any]) -> dict[str, Any]:
        score = 0.46
        if "payment" in str(context.get("strongest_content_signal", "")):
            score += 0.08
        return RuntimeStrategySimulation._scenario(
            "SIM-003",
            "strengthen_korea_market",
            "If AGOS strengthens Korea market localization.",
            score,
            0.38,
            "Potential upside exists, but current strongest local evidence is Japan travel. Korea should stay a controlled expansion test.",
            "Create a small Korea-localized test batch before changing main priority.",
        )

    @staticmethod
    def _simulate_stop_failed_strategy(context: dict[str, Any]) -> dict[str, Any]:
        return RuntimeStrategySimulation._scenario(
            "SIM-004",
            "stop_failed_generic_strategy",
            "If AGOS stops generic replies and failed hook reuse.",
            0.72,
            0.18,
            "Likely improves learning quality because failed patterns have already been marked as avoid without review.",
            "Block generic reply patterns unless a human rewrites them.",
        )

    @staticmethod
    def _scenario(
        scenario_id: str,
        scenario: str,
        hypothesis: str,
        predicted_growth_score: float,
        risk_score: float,
        predicted_outcome: str,
        recommendation: str,
    ) -> dict[str, Any]:
        net = max(predicted_growth_score - risk_score * 0.35, 0)
        return {
            "scenario_id": scenario_id,
            "scenario": scenario,
            "hypothesis": hypothesis,
            "predicted_growth_score": round(predicted_growth_score, 3),
            "risk_score": round(risk_score, 3),
            "net_strategy_score": round(net, 3),
            "predicted_outcome": predicted_outcome,
            "recommendation": recommendation,
            "review_status": "needs_human_review",
            "simulation_only": True,
        }

    @staticmethod
    def _feed(scenarios: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "time": utc_now_iso(),
                "scenario": item["scenario"],
                "rank": rank,
                "net_strategy_score": item["net_strategy_score"],
                "predicted_outcome": item["predicted_outcome"],
                "recommendation": item["recommendation"],
                "status": item["review_status"],
            }
            for rank, item in enumerate(sorted(scenarios, key=lambda row: row["net_strategy_score"], reverse=True), start=1)
        ]

    @staticmethod
    def _best_scenario(scenarios: list[dict[str, Any]]) -> str:
        if not scenarios:
            return "none"
        return max(scenarios, key=lambda item: item["net_strategy_score"])["scenario"]

    @staticmethod
    def _highest_risk(scenarios: list[dict[str, Any]]) -> str:
        if not scenarios:
            return "none"
        return max(scenarios, key=lambda item: item["risk_score"])["scenario"]


if __name__ == "__main__":
    result = RuntimeStrategySimulation().simulate()
    print(
        json.dumps(
            {
                "status": result["status"],
                "best": result["simulationSummary"]["best_scenario"],
                "scenarios": len(result["strategySimulationScenarios"]),
            },
            indent=2,
        )
    )
