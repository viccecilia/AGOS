"""Long-term strategy memory for AGOS autonomous growth preparation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.failure_analysis_engine import FailureAnalysisEngine
from services.heat_detection_engine import HeatDetectionEngine
from services.real_feedback_capture_engine import RealFeedbackCaptureEngine
from services.runtime_persistence import utc_now_iso
from services.strategy_evolution_engine import StrategyEvolutionEngine
from services.trend_clustering_engine import TrendClusteringEngine


class LongTermStrategyMemory:
    """Persist durable strategy memory beyond single feedback events."""

    def __init__(self, root: str | Path = "runtime/long_term_strategy_memory") -> None:
        self.root = Path(root)
        self.report_path = self.root / "LONG_TERM_STRATEGY_MEMORY_REPORT.json"
        self.memory_path = self.root / "long_term_strategy_memory.json"
        self.timeline_path = self.root / "strategy_memory_timeline.json"

    def build(self) -> dict[str, Any]:
        strategy_evolution = StrategyEvolutionEngine().state()
        feedback = RealFeedbackCaptureEngine().state()
        failures = FailureAnalysisEngine().state()
        trends = TrendClusteringEngine().state()
        heat = HeatDetectionEngine().state()

        evolution_items = strategy_evolution.get("longTermGrowthStrategies", []) + strategy_evolution.get(
            "shortTermTrafficTactics", []
        )
        long_term_effective = [self._memory_item(item, "long_term_effective") for item in evolution_items if item.get("classification") == "long_term_growth"]
        short_term_effective = [self._memory_item(item, "short_term_effective") for item in evolution_items if item.get("classification") == "short_term_traffic"]
        long_term_failed = [self._failure_memory(item) for item in failures.get("failureItems", [])]
        platform_trends = self._platform_trends(trends, heat, feedback)
        market_trends = self._market_trends(trends, heat)
        report = {
            "report_id": "LONG_TERM_STRATEGY_MEMORY_REPORT",
            "created_at": utc_now_iso(),
            "status": "forming_long_term_memory" if long_term_effective else "needs_more_evidence",
            "scope": "local_autonomous_growth_preparation_only",
            "longTermEffectiveStrategies": long_term_effective,
            "shortTermEffectiveStrategies": short_term_effective,
            "longTermFailedStrategies": long_term_failed,
            "platformLongTermTrends": platform_trends,
            "marketLongTermTrends": market_trends,
            "strategyHorizonClassification": {
                "long_term_growth_count": len(long_term_effective),
                "short_term_traffic_count": len(short_term_effective),
                "long_term_failure_count": len(long_term_failed),
                "can_distinguish_short_vs_long": bool(long_term_effective and short_term_effective),
                "primary_long_term_direction": self._primary_direction(long_term_effective),
                "avoid_overweighting": [item["platform"] for item in short_term_effective if item.get("risk", 0) >= 0.35],
            },
            "strategyMemoryTimeline": self._timeline(long_term_effective, short_term_effective, long_term_failed),
        }
        self.persist(report)
        return report

    def state(self) -> dict[str, Any]:
        if self.report_path.exists():
            return json.loads(self.report_path.read_text(encoding="utf-8"))
        return self.build()

    def persist(self, report: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.memory_path.write_text(
            json.dumps(
                {
                    "longTermEffectiveStrategies": report["longTermEffectiveStrategies"],
                    "shortTermEffectiveStrategies": report["shortTermEffectiveStrategies"],
                    "longTermFailedStrategies": report["longTermFailedStrategies"],
                    "strategyHorizonClassification": report["strategyHorizonClassification"],
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        self.timeline_path.write_text(
            json.dumps(report["strategyMemoryTimeline"], ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    @staticmethod
    def _memory_item(item: dict[str, Any], memory_type: str) -> dict[str, Any]:
        durable = item.get("durable_score", 0)
        spike = item.get("spike_score", 0)
        return {
            "memory_id": f"{memory_type}_{item.get('signal_id', item.get('platform', 'unknown'))}",
            "memory_type": memory_type,
            "platform": item.get("platform", "unknown"),
            "strategy": item.get("strategy", ""),
            "time_horizon": "long_term_growth" if memory_type == "long_term_effective" else "short_term_traffic",
            "durable_score": durable,
            "spike_score": spike,
            "risk": item.get("risk", 0),
            "reason": item.get("reason", ""),
            "next_action": (
                "Promote into durable operating memory and retest over multiple cycles."
                if memory_type == "long_term_effective"
                else "Keep as an experiment; do not let traffic spikes override long-term trust."
            ),
            "human_review_status": item.get("human_review_status", "needs_human_review"),
        }

    @staticmethod
    def _failure_memory(item: dict[str, Any]) -> dict[str, Any]:
        return {
            "memory_id": "failed_" + str(item.get("failure_id", "unknown")),
            "memory_type": "long_term_failed_strategy",
            "platform": item.get("platform", "unknown"),
            "failure_type": item.get("failure_type", "unknown"),
            "failed_pattern": item.get("strategy") or item.get("hook") or item.get("reply_text", ""),
            "why_failed": item.get("why_failed", ""),
            "avoid_rule": item.get("fix_recommendation", "Do not reuse without human review."),
            "human_review_status": "needs_human_review",
        }

    @staticmethod
    def _platform_trends(trends: dict[str, Any], heat: dict[str, Any], feedback: dict[str, Any]) -> list[dict[str, Any]]:
        heat_by_platform: dict[str, list[dict[str, Any]]] = {}
        for item in heat.get("opportunityRanking", []):
            for platform in item.get("platforms", []) or [item.get("platform", "unknown")]:
                heat_by_platform.setdefault(platform, []).append(item)
        feedback_events = feedback.get("feedbackEvents", [])
        rows = []
        for platform, signals in sorted(heat_by_platform.items()):
            positives = [event for event in feedback_events if event.get("platform") == platform and event.get("has_positive_feedback")]
            rows.append(
                {
                    "platform": platform,
                    "trend_count": len(signals),
                    "positive_feedback_count": len(positives),
                    "long_term_signal": "durable" if positives or len(signals) >= 2 else "watch",
                    "dominant_trends": [item.get("cluster_name") or item.get("pain_point") for item in signals[:3]],
                }
            )
        if rows:
            return rows
        return [
            {
                "platform": "local_runtime",
                "trend_count": len(trends.get("trendClusters", [])),
                "positive_feedback_count": len(feedback_events),
                "long_term_signal": "watch",
                "dominant_trends": [item.get("cluster_name") for item in trends.get("trendClusters", [])[:3]],
            }
        ]

    @staticmethod
    def _market_trends(trends: dict[str, Any], heat: dict[str, Any]) -> list[dict[str, Any]]:
        clusters = trends.get("trendClusters", [])
        hot = heat.get("heatSignals", [])
        return [
            {
                "market": "Japan",
                "trend_count": len(clusters),
                "hot_signal_count": len([item for item in hot if item.get("heat_level") in {"hot", "warming"}]),
                "long_term_trend": "travel anxiety and local navigation confidence",
                "reason": "Repeated travel pain points are stable enough for evergreen guidance and trust-building content.",
            }
        ]

    @staticmethod
    def _primary_direction(long_term: list[dict[str, Any]]) -> str:
        if not long_term:
            return "No durable long-term strategy confirmed yet."
        best = sorted(long_term, key=lambda item: item.get("durable_score", 0), reverse=True)[0]
        return f"{best['platform']}: {best['strategy']}"

    @staticmethod
    def _timeline(
        long_term: list[dict[str, Any]],
        short_term: list[dict[str, Any]],
        failed: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for item in long_term:
            rows.append(
                {
                    "time": utc_now_iso(),
                    "type": "long_term_growth_memory",
                    "platform": item["platform"],
                    "summary": item["strategy"],
                    "status": "stored",
                }
            )
        for item in short_term:
            rows.append(
                {
                    "time": utc_now_iso(),
                    "type": "short_term_traffic_memory",
                    "platform": item["platform"],
                    "summary": item["strategy"],
                    "status": "experimental",
                }
            )
        for item in failed:
            rows.append(
                {
                    "time": utc_now_iso(),
                    "type": "failed_strategy_memory",
                    "platform": item["platform"],
                    "summary": item["why_failed"],
                    "status": "avoid_without_review",
                }
            )
        return rows


if __name__ == "__main__":
    result = LongTermStrategyMemory().build()
    print(
        json.dumps(
            {
                "status": result["status"],
                "long_term": len(result["longTermEffectiveStrategies"]),
                "short_term": len(result["shortTermEffectiveStrategies"]),
                "failed": len(result["longTermFailedStrategies"]),
            },
            indent=2,
        )
    )
