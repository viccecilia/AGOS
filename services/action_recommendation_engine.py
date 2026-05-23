"""Action recommendations for the AGOS semi-autonomous runtime stage."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.autonomous_growth_preparation_gate import AutonomousGrowthPreparationGate
from services.growth_signal_correlation_engine import GrowthSignalCorrelationEngine
from services.personality_memory_deposit import PersonalityMemoryDeposit
from services.runtime_persistence import utc_now_iso
from services.runtime_priority_engine import RuntimePriorityEngine
from services.runtime_strategy_simulation import RuntimeStrategySimulation


class ActionRecommendationEngine:
    """Generate human-gated operating recommendations from AGOS intelligence."""

    def __init__(self, root: str | Path = "runtime/action_recommendations") -> None:
        self.root = Path(root)
        self.report_path = self.root / "ACTION_RECOMMENDATION_REPORT.json"
        self.recommendations_path = self.root / "action_recommendations.json"
        self.feed_path = self.root / "action_recommendation_feed.json"

    def recommend(self) -> dict[str, Any]:
        gate = AutonomousGrowthPreparationGate().state()
        priority = RuntimePriorityEngine().state()
        correlation = GrowthSignalCorrelationEngine().state()
        simulation = RuntimeStrategySimulation().state()
        personality = PersonalityMemoryDeposit().status()

        recommendations = [
            self._content_recommendation(priority, correlation, simulation, personality),
            self._reply_recommendation(priority, correlation, personality),
            self._platform_recommendation(priority, simulation, personality),
            self._trend_recommendation(priority, correlation, personality),
        ]
        report = {
            "report_id": "ACTION_RECOMMENDATION_REPORT",
            "created_at": utc_now_iso(),
            "status": "recommendations_ready",
            "scope": "local_human_gated_recommendations_only",
            "sourceGate": gate.get("status", "unknown"),
            "actionRecommendations": recommendations,
            "actionRecommendationFeed": self._feed(recommendations),
            "recommendationSummary": {
                "total_recommendations": len(recommendations),
                "high_priority": len([item for item in recommendations if item["priority"] == "high"]),
                "requires_human_review": True,
                "top_action": recommendations[0]["action_id"] if recommendations else "none",
            },
            "safetyBoundary": "Recommendations do not post, reply, register accounts, log in, or call platform APIs.",
        }
        self.persist(report)
        return report

    def state(self) -> dict[str, Any]:
        if self.report_path.exists():
            return json.loads(self.report_path.read_text(encoding="utf-8"))
        return self.recommend()

    def persist(self, report: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.recommendations_path.write_text(
            json.dumps(report["actionRecommendations"], ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        self.feed_path.write_text(
            json.dumps(report["actionRecommendationFeed"], ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    @staticmethod
    def _content_recommendation(
        priority: dict[str, Any],
        correlation: dict[str, Any],
        simulation: dict[str, Any],
        personality: dict[str, Any],
    ) -> dict[str, Any]:
        summary = correlation.get("correlationSummary", {})
        sim = simulation.get("simulationSummary", {})
        top_question = priority.get("prioritySummary", {}).get("top_question", "Tokyo transport anxiety")
        content_signal = summary.get("strongest_content_signal", "transport_anxiety_guidance")
        return ActionRecommendationEngine._recommendation(
            "REC-CONTENT-001",
            "today_content",
            f"Create one human-reviewed {content_signal} content draft around {top_question}.",
            f"{content_signal} is the strongest content signal and {sim.get('best_scenario', 'increase_reddit_content')} is the best simulated strategy.",
            "medium",
            "Higher save/reply potential from a durable guidance format.",
            "Reddit",
            ActionRecommendationEngine._best_personality(personality),
            "Japan",
            "high",
        )

    @staticmethod
    def _reply_recommendation(
        priority: dict[str, Any],
        correlation: dict[str, Any],
        personality: dict[str, Any],
    ) -> dict[str, Any]:
        strongest_hook = correlation.get("correlationSummary", {}).get("strongest_hook_signal", "make payment decision simple")
        top_question = priority.get("prioritySummary", {}).get("top_question", "Tokyo transport anxiety")
        return ActionRecommendationEngine._recommendation(
            "REC-REPLY-001",
            "today_reply",
            f"Draft two replies using hook '{strongest_hook}' for {top_question}.",
            f"The hook {strongest_hook} is currently the strongest interaction signal.",
            "medium",
            "More useful reply drafts with better chance of positive feedback.",
            "Reddit",
            ActionRecommendationEngine._best_personality(personality),
            "Japan",
            "high",
        )

    @staticmethod
    def _platform_recommendation(
        priority: dict[str, Any],
        simulation: dict[str, Any],
        personality: dict[str, Any],
    ) -> dict[str, Any]:
        top_platform = priority.get("prioritySummary", {}).get("top_platform", "reddit")
        best_scenario = simulation.get("simulationSummary", {}).get("best_scenario", "increase_reddit_content")
        return ActionRecommendationEngine._recommendation(
            "REC-PLATFORM-001",
            "today_platform",
            f"Prioritize {top_platform} today and keep TikTok in experiment mode.",
            f"{top_platform} is the current top platform and {best_scenario} is the best simulated scenario.",
            "low",
            "More durable trust-building signal with lower drift risk.",
            top_platform,
            ActionRecommendationEngine._best_personality(personality),
            "Japan",
            "high",
        )

    @staticmethod
    def _trend_recommendation(
        priority: dict[str, Any],
        correlation: dict[str, Any],
        personality: dict[str, Any],
    ) -> dict[str, Any]:
        top_trend = priority.get("prioritySummary", {}).get("top_trend", "Tokyo transport anxiety")
        content_signal = correlation.get("correlationSummary", {}).get("strongest_content_signal", "transport_anxiety_guidance")
        return ActionRecommendationEngine._recommendation(
            "REC-TREND-001",
            "today_trend",
            f"Track and draft around trend '{top_trend}' with {content_signal}.",
            f"{top_trend} is the current top trend and matches the strongest content correlation.",
            "medium",
            "Better alignment between scout signal and content strategy.",
            "Reddit",
            ActionRecommendationEngine._best_personality(personality),
            "Japan",
            "medium",
        )

    @staticmethod
    def _recommendation(
        action_id: str,
        action_type: str,
        recommendation: str,
        why_recommended: str,
        risk_level: str,
        expected_result: str,
        recommended_platform: str,
        recommended_personality: str,
        recommended_market: str,
        priority: str,
    ) -> dict[str, Any]:
        return {
            "action_id": action_id,
            "action_type": action_type,
            "recommendation": recommendation,
            "why_recommended": why_recommended,
            "risk_level": risk_level,
            "expected_result": expected_result,
            "recommended_platform": recommended_platform,
            "recommended_personality": recommended_personality,
            "recommended_market": recommended_market,
            "priority": priority,
            "review_status": "needs_human_review",
            "execution_boundary": "local recommendation only; no external action",
        }

    @staticmethod
    def _feed(recommendations: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "time": utc_now_iso(),
                "type": item["action_type"],
                "action_id": item["action_id"],
                "recommendation": item["recommendation"],
                "why_recommended": item["why_recommended"],
                "risk_level": item["risk_level"],
                "expected_result": item["expected_result"],
                "platform": item["recommended_platform"],
                "personality": item["recommended_personality"],
                "market": item["recommended_market"],
                "status": item["review_status"],
            }
            for item in recommendations
        ]

    @staticmethod
    def _best_personality(personality: dict[str, Any]) -> str:
        best = personality.get("bestPersonality") or {}
        return best.get("tone") or "trusted_guide"


if __name__ == "__main__":
    result = ActionRecommendationEngine().recommend()
    print(
        json.dumps(
            {
                "status": result["status"],
                "recommendations": len(result["actionRecommendations"]),
            },
            indent=2,
        )
    )
