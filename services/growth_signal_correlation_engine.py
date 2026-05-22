"""Growth signal correlation for AGOS autonomous growth preparation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.best_answer_learning_engine import BestAnswerLearningEngine
from services.personality_memory_deposit import PersonalityMemoryDeposit
from services.real_feedback_capture_engine import RealFeedbackCaptureEngine
from services.runtime_persistence import utc_now_iso
from services.runtime_priority_engine import RuntimePriorityEngine


class GrowthSignalCorrelationEngine:
    """Correlate actions with feedback and growth signals."""

    def __init__(self, root: str | Path = "runtime/signal_correlation") -> None:
        self.root = Path(root)
        self.report_path = self.root / "GROWTH_SIGNAL_CORRELATION_REPORT.json"
        self.matrix_path = self.root / "signal_correlation_matrix.json"
        self.feed_path = self.root / "growth_signal_correlation_feed.json"

    def correlate(self) -> dict[str, Any]:
        feedback = RealFeedbackCaptureEngine().state()
        learning = BestAnswerLearningEngine().state()
        personality = PersonalityMemoryDeposit().status()
        priority = RuntimePriorityEngine().state()

        events = feedback.get("feedbackEvents", [])
        scored_events = [self._score_event(event) for event in events]
        content_rows = self._content_correlations(scored_events)
        platform_rows = self._platform_correlations(scored_events, priority)
        hook_rows = self._hook_correlations(learning)
        personality_rows = self._personality_correlations(personality, scored_events)
        matrix = {
            "content_to_feedback": content_rows,
            "platform_to_growth": platform_rows,
            "hook_to_interaction": hook_rows,
            "personality_to_result": personality_rows,
        }
        feed = self._feed(matrix)
        report = {
            "report_id": "GROWTH_SIGNAL_CORRELATION_REPORT",
            "created_at": utc_now_iso(),
            "status": "correlating_growth_signals",
            "scope": "local_signal_correlation_only",
            "signalCorrelationMatrix": matrix,
            "growthSignalCorrelationFeed": feed,
            "correlationSummary": {
                "strongest_content_signal": self._top_signal(content_rows, "content_type"),
                "strongest_platform_signal": self._top_signal(platform_rows, "platform"),
                "strongest_hook_signal": self._top_signal(hook_rows, "hook"),
                "strongest_personality_signal": self._top_signal(personality_rows, "personality"),
                "can_explain_growth_behavior": bool(feed),
            },
            "safetyBoundary": "Correlation only informs local planning and human-reviewed drafts.",
        }
        self.persist(report)
        return report

    def state(self) -> dict[str, Any]:
        if self.report_path.exists():
            return json.loads(self.report_path.read_text(encoding="utf-8"))
        return self.correlate()

    def persist(self, report: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.matrix_path.write_text(
            json.dumps(report["signalCorrelationMatrix"], ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        self.feed_path.write_text(
            json.dumps(report["growthSignalCorrelationFeed"], ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    @staticmethod
    def _score_event(event: dict[str, Any]) -> dict[str, Any]:
        score = 0
        score += 2 if event.get("liked") else 0
        score += 3 if event.get("replied") else 0
        score += 3 if event.get("saved") else 0
        score += 4 if event.get("shared") else 0
        score -= 2 if event.get("ignored") else 0
        return {
            **event,
            "growth_score": score,
            "content_type": GrowthSignalCorrelationEngine._content_type(event),
        }

    @staticmethod
    def _content_type(event: dict[str, Any]) -> str:
        text = (event.get("question_text", "") + " " + event.get("reply_text", "")).lower()
        if "suica" in text or "cash" in text or "card" in text:
            return "payment_decision_guidance"
        if "station" in text or "train" in text or "subway" in text:
            return "transport_anxiety_guidance"
        if "rain" in text or "weather" in text:
            return "weather_friction_guidance"
        return "general_travel_guidance"

    @staticmethod
    def _aggregate(rows: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
        grouped: dict[str, list[dict[str, Any]]] = {}
        for row in rows:
            grouped.setdefault(str(row.get(key, "unknown")), []).append(row)
        results = []
        for name, items in grouped.items():
            positives = len([item for item in items if item.get("has_positive_feedback")])
            ignored = len([item for item in items if item.get("ignored")])
            score = sum(float(item.get("growth_score", 0)) for item in items)
            results.append(
                {
                    key: name,
                    "events": len(items),
                    "positive_feedback": positives,
                    "ignored": ignored,
                    "growth_score": round(score, 3),
                    "correlation_strength": GrowthSignalCorrelationEngine._strength(score, len(items)),
                    "why_it_matters": f"{name} produced {positives} positive signal(s), {ignored} ignored signal(s), and score {round(score, 3)}.",
                }
            )
        return sorted(results, key=lambda item: item["growth_score"], reverse=True)

    @staticmethod
    def _content_correlations(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        rows = GrowthSignalCorrelationEngine._aggregate(events, "content_type")
        for row in rows:
            row["growth_result"] = "repeatable_content_candidate" if row["growth_score"] > 0 else "needs_revision"
        return rows

    @staticmethod
    def _platform_correlations(events: list[dict[str, Any]], priority: dict[str, Any]) -> list[dict[str, Any]]:
        rows = GrowthSignalCorrelationEngine._aggregate(events, "platform")
        priority_by_platform = {item.get("platform", ""): item for item in priority.get("platformPriority", [])}
        for row in rows:
            platform_priority = priority_by_platform.get(row["platform"].lower(), {})
            row["priority"] = platform_priority.get("priority", "watch")
            row["priority_reason"] = platform_priority.get("why_changed", "")
            row["growth_result"] = "growth_platform_candidate" if row["growth_score"] > 0 and row["priority"] in {"high", "medium"} else "watch_or_experiment"
        return rows

    @staticmethod
    def _hook_correlations(learning: dict[str, Any]) -> list[dict[str, Any]]:
        memory = learning.get("bestAnswerLearning", {})
        rows = []
        best_hook = memory.get("bestHook")
        if best_hook and best_hook != "none":
            rows.append(
                {
                    "hook": best_hook,
                    "events": 1,
                    "positive_feedback": 1,
                    "ignored": 0,
                    "growth_score": 1.0,
                    "correlation_strength": "strong",
                    "interaction_result": "best_hook_candidate",
                    "why_it_matters": f"{best_hook} is associated with the current best answer.",
                }
            )
        for hook in memory.get("failedHooks", []):
            rows.append(
                {
                    "hook": hook,
                    "events": 1,
                    "positive_feedback": 0,
                    "ignored": 1,
                    "growth_score": -1.0,
                    "correlation_strength": "negative",
                    "interaction_result": "avoid_without_revision",
                    "why_it_matters": f"{hook} appeared in failed or ignored answer learning.",
                }
            )
        return sorted(rows, key=lambda item: item["growth_score"], reverse=True)

    @staticmethod
    def _personality_correlations(personality: dict[str, Any], events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        rows = []
        best = personality.get("bestPersonality") or {}
        failed = personality.get("failedPersonality") or {}
        if best:
            platform = best.get("platform", "unknown")
            positives = len([event for event in events if event.get("platform", "").lower() == platform.lower() and event.get("has_positive_feedback")])
            rows.append(
                {
                    "personality": best.get("tone", "approved_personality"),
                    "platform": platform,
                    "result": "approved_growth_style",
                    "positive_feedback": positives,
                    "growth_score": round(0.7 + positives * 0.1, 3),
                    "correlation_strength": "strong" if positives else "medium",
                    "why_it_matters": best.get("reason", "Approved personality aligns with desired operating style."),
                }
            )
        if failed:
            rows.append(
                {
                    "personality": failed.get("tone", "failed_personality"),
                    "platform": failed.get("platform", "unknown"),
                    "result": "style_to_avoid",
                    "positive_feedback": 0,
                    "growth_score": -0.5,
                    "correlation_strength": "negative",
                    "why_it_matters": failed.get("reason", "Rejected personality should not guide autonomous strategy."),
                }
            )
        return sorted(rows, key=lambda item: item["growth_score"], reverse=True)

    @staticmethod
    def _feed(matrix: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
        feed = []
        for group, rows in matrix.items():
            for rank, row in enumerate(rows[:4], start=1):
                target = row.get("content_type") or row.get("platform") or row.get("hook") or row.get("personality")
                feed.append(
                    {
                        "time": utc_now_iso(),
                        "type": group,
                        "rank": rank,
                        "target": target,
                        "growth_score": row.get("growth_score", 0),
                        "correlation_strength": row.get("correlation_strength", "watch"),
                        "why_it_matters": row.get("why_it_matters", ""),
                        "ai_action": GrowthSignalCorrelationEngine._action_for(row),
                        "status": "human_review_required" if row.get("growth_score", 0) > 0 else "needs_revision",
                    }
                )
        return feed

    @staticmethod
    def _action_for(row: dict[str, Any]) -> str:
        if float(row.get("growth_score", 0)) > 0:
            return "Promote into human-reviewed strategy candidate."
        return "Revise or avoid before reuse."

    @staticmethod
    def _strength(score: float, events: int) -> str:
        if score <= 0:
            return "negative"
        if score / max(events, 1) >= 4:
            return "strong"
        if score / max(events, 1) >= 2:
            return "medium"
        return "weak"

    @staticmethod
    def _top_signal(rows: list[dict[str, Any]], key: str) -> str:
        if not rows:
            return "none"
        return str(rows[0].get(key, "none"))


if __name__ == "__main__":
    result = GrowthSignalCorrelationEngine().correlate()
    print(
        json.dumps(
            {
                "status": result["status"],
                "feed_items": len(result["growthSignalCorrelationFeed"]),
                "strongest_platform": result["correlationSummary"]["strongest_platform_signal"],
            },
            indent=2,
        )
    )
