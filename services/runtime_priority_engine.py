"""Runtime priority evolution for AGOS autonomous growth preparation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.failure_analysis_engine import FailureAnalysisEngine
from services.heat_detection_engine import HeatDetectionEngine
from services.long_term_strategy_memory import LongTermStrategyMemory
from services.real_feedback_capture_engine import RealFeedbackCaptureEngine
from services.runtime_persistence import utc_now_iso


class RuntimePriorityEngine:
    """Dynamically adjust operational priority across platforms, questions, trends, and content."""

    def __init__(self, root: str | Path = "runtime/runtime_priority") -> None:
        self.root = Path(root)
        self.report_path = self.root / "RUNTIME_PRIORITY_REPORT.json"
        self.feed_path = self.root / "runtime_priority_feed.json"
        self.history_path = self.root / "priority_evolution_history.json"

    def evolve(self) -> dict[str, Any]:
        heat = HeatDetectionEngine().state()
        memory = LongTermStrategyMemory().state()
        feedback = RealFeedbackCaptureEngine().state()
        failures = FailureAnalysisEngine().state()

        platform_priority = self._platform_priority(heat, memory, feedback, failures)
        question_priority = self._question_priority(heat, memory)
        trend_priority = self._trend_priority(heat, memory)
        content_priority = self._content_priority(memory, failures)
        history = self._history(platform_priority, question_priority, trend_priority, content_priority)
        feed = self._feed(history)
        report = {
            "report_id": "RUNTIME_PRIORITY_REPORT",
            "created_at": utc_now_iso(),
            "status": "priority_evolving",
            "scope": "local_autonomous_growth_preparation_only",
            "platformPriority": platform_priority,
            "questionPriority": question_priority,
            "trendPriority": trend_priority,
            "contentPriority": content_priority,
            "priorityEvolutionHistory": history,
            "runtimePriorityFeed": feed,
            "prioritySummary": {
                "top_platform": platform_priority[0]["platform"] if platform_priority else "none",
                "top_question": question_priority[0]["question_focus"] if question_priority else "none",
                "top_trend": trend_priority[0]["trend"] if trend_priority else "none",
                "top_content": content_priority[0]["content_focus"] if content_priority else "none",
                "can_explain_priority_change": bool(feed),
            },
            "safetyBoundary": "Priority changes only affect local planning and human-reviewed drafts.",
        }
        self.persist(report)
        return report

    def state(self) -> dict[str, Any]:
        if self.report_path.exists():
            return json.loads(self.report_path.read_text(encoding="utf-8"))
        return self.evolve()

    def persist(self, report: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.feed_path.write_text(json.dumps(report["runtimePriorityFeed"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.history_path.write_text(
            json.dumps(report["priorityEvolutionHistory"], ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    @staticmethod
    def _platform_priority(
        heat: dict[str, Any],
        memory: dict[str, Any],
        feedback: dict[str, Any],
        failures: dict[str, Any],
    ) -> list[dict[str, Any]]:
        heat_scores: dict[str, float] = {}
        for item in heat.get("opportunityRanking", []):
            for platform in item.get("platforms", []) or [item.get("platform", "unknown")]:
                heat_scores[platform.lower()] = max(heat_scores.get(platform.lower(), 0), float(item.get("opportunity_score", 0)))

        durable_platforms = {
            item.get("platform", "").lower(): float(item.get("durable_score", 0))
            for item in memory.get("longTermEffectiveStrategies", [])
        }
        avoid = set(memory.get("strategyHorizonClassification", {}).get("avoid_overweighting", []))
        feedback_events = feedback.get("feedbackEvents", [])
        failure_items = failures.get("failureItems", [])
        platforms = set(heat_scores) | set(durable_platforms) | {event.get("platform", "").lower() for event in feedback_events}
        rows = []
        for platform in sorted(item for item in platforms if item):
            positive = len([event for event in feedback_events if event.get("platform", "").lower() == platform and event.get("has_positive_feedback")])
            failed = len([item for item in failure_items if item.get("platform", "").lower() == platform])
            score = heat_scores.get(platform, 0) * 0.45 + durable_platforms.get(platform, 0) * 0.4 + positive * 0.08 - failed * 0.05
            if platform in avoid:
                score -= 0.12
            reason = RuntimePriorityEngine._platform_reason(platform, heat_scores.get(platform, 0), durable_platforms.get(platform, 0), positive, failed, platform in avoid)
            rows.append(
                {
                    "platform": platform,
                    "priority_score": round(max(score, 0), 3),
                    "priority": RuntimePriorityEngine._priority_label(score),
                    "why_changed": reason,
                    "next_action": "Prioritize human-reviewed strategy work." if score >= 0.5 else "Keep as watch or experiment.",
                }
            )
        return sorted(rows, key=lambda item: item["priority_score"], reverse=True)

    @staticmethod
    def _question_priority(heat: dict[str, Any], memory: dict[str, Any]) -> list[dict[str, Any]]:
        primary = memory.get("strategyHorizonClassification", {}).get("primary_long_term_direction", "")
        rows = []
        for item in heat.get("opportunityRanking", []):
            score = float(item.get("opportunity_score", 0)) * 0.75 + min(float(item.get("frequency", 0)) / 10, 0.2)
            if "transport" in (item.get("cluster_name", "").lower() + primary.lower()):
                score += 0.08
            rows.append(
                {
                    "question_focus": item.get("cluster_name") or item.get("pain_point") or item.get("cluster_id"),
                    "priority_score": round(score, 3),
                    "priority": RuntimePriorityEngine._priority_label(score),
                    "why_changed": item.get("why_hot") or "Question priority changed because heat score and durable memory changed.",
                    "next_action": item.get("recommended_action", "Prepare human-reviewed answer branch."),
                }
            )
        return sorted(rows, key=lambda item: item["priority_score"], reverse=True)

    @staticmethod
    def _trend_priority(heat: dict[str, Any], memory: dict[str, Any]) -> list[dict[str, Any]]:
        long_term_markets = memory.get("marketLongTermTrends", [])
        rows = []
        for item in heat.get("heatSignals", []):
            score = float(item.get("opportunity_score", 0))
            if long_term_markets and item.get("heat_level") == "hot":
                score += 0.06
            rows.append(
                {
                    "trend": item.get("cluster_name") or item.get("cluster_id"),
                    "priority_score": round(score, 3),
                    "priority": RuntimePriorityEngine._priority_label(score),
                    "why_changed": item.get("why_hot", "Trend priority changed because heat and market memory shifted."),
                    "next_action": "Move into strategy and content planning if human review approves.",
                }
            )
        return sorted(rows, key=lambda item: item["priority_score"], reverse=True)

    @staticmethod
    def _content_priority(memory: dict[str, Any], failures: dict[str, Any]) -> list[dict[str, Any]]:
        rows = []
        for item in memory.get("longTermEffectiveStrategies", []):
            rows.append(
                {
                    "content_focus": f"{item.get('platform')} durable guidance",
                    "priority_score": round(float(item.get("durable_score", 0)) + 0.08, 3),
                    "priority": RuntimePriorityEngine._priority_label(float(item.get("durable_score", 0)) + 0.08),
                    "why_changed": "Durable strategy memory is stronger than short-term traffic for this content type.",
                    "next_action": item.get("next_action", "Promote into durable content memory."),
                }
            )
        failed_count = len(failures.get("failureItems", []))
        rows.append(
            {
                "content_focus": "avoid failed hooks and generic replies",
                "priority_score": round(min(0.35 + failed_count * 0.08, 0.9), 3),
                "priority": "high" if failed_count >= 3 else "medium",
                "why_changed": f"{failed_count} failed pattern(s) were detected; correction work must stay visible.",
                "next_action": "Require human review before reusing failed patterns.",
            }
        )
        return sorted(rows, key=lambda item: item["priority_score"], reverse=True)

    @staticmethod
    def _history(
        platforms: list[dict[str, Any]],
        questions: list[dict[str, Any]],
        trends: list[dict[str, Any]],
        contents: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        rows = []
        groups = [
            ("platform_priority", platforms, "platform"),
            ("question_priority", questions, "question_focus"),
            ("trend_priority", trends, "trend"),
            ("content_priority", contents, "content_focus"),
        ]
        for priority_type, items, key in groups:
            for rank, item in enumerate(items[:5], start=1):
                rows.append(
                    {
                        "timestamp": utc_now_iso(),
                        "priority_type": priority_type,
                        "rank": rank,
                        "target": item.get(key, "unknown"),
                        "priority_score": item.get("priority_score", 0),
                        "priority": item.get("priority", "watch"),
                        "why_changed": item.get("why_changed", ""),
                        "next_action": item.get("next_action", ""),
                    }
                )
        return rows

    @staticmethod
    def _feed(history: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "time": item["timestamp"],
                "type": item["priority_type"],
                "target": item["target"],
                "priority": item["priority"],
                "rank": item["rank"],
                "why_changed": item["why_changed"],
                "ai_action": item["next_action"],
                "status": "human_review_required" if item["priority"] == "high" else "watch",
            }
            for item in history
        ]

    @staticmethod
    def _priority_label(score: float) -> str:
        if score >= 0.72:
            return "high"
        if score >= 0.45:
            return "medium"
        return "watch"

    @staticmethod
    def _platform_reason(platform: str, heat: float, durable: float, positive: int, failed: int, avoid: bool) -> str:
        parts = [f"heat={round(heat, 3)}", f"durable_memory={round(durable, 3)}"]
        if positive:
            parts.append(f"positive_feedback={positive}")
        if failed:
            parts.append(f"failures={failed}")
        if avoid:
            parts.append("long_term_memory_warns_not_to_overweight")
        return f"{platform} priority changed because " + ", ".join(parts) + "."


if __name__ == "__main__":
    result = RuntimePriorityEngine().evolve()
    print(
        json.dumps(
            {
                "status": result["status"],
                "top_platform": result["prioritySummary"]["top_platform"],
                "feed_items": len(result["runtimePriorityFeed"]),
            },
            indent=2,
        )
    )
