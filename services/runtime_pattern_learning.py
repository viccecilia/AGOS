"""Runtime pattern learning from batch human review signals."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from services.batch_human_review import BatchHumanReview
from services.runtime_persistence import utc_now_iso


PATTERN_TYPES = ["high_value", "high_engagement", "high_conversion", "high_risk"]


class RuntimePatternLearning:
    """Learn result patterns from reviewed question clusters."""

    def __init__(self, root: str | Path = "runtime/pattern_memory") -> None:
        self.root = Path(root)
        self.report_path = self.root / "RUNTIME_PATTERN_LEARNING_REPORT.json"
        self.pattern_memory_path = self.root / "pattern_memory.json"
        self.pattern_feed_path = self.root / "runtime_pattern_feed.json"
        self.pattern_summary_path = self.root / "pattern_learning_summary.json"

    def learn(self, review_queue: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        reviews = review_queue
        if reviews is None:
            reviews = BatchHumanReview().state().get("batchReviewQueue", [])
        pattern_memory = [self._pattern_record(index, item) for index, item in enumerate(reviews, start=1)]
        feed = self._feed(pattern_memory)
        summary = self._summary(pattern_memory, reviews)
        report = {
            "report_id": "RUNTIME_PATTERN_LEARNING_REPORT",
            "created_at": utc_now_iso(),
            "status": "runtime_patterns_learned",
            "scope": "local_runtime_pattern_learning",
            "patternTypes": PATTERN_TYPES,
            "patternMemory": pattern_memory,
            "runtimePatternFeed": feed,
            "patternLearningSummary": summary,
            "safetyBoundary": "Runtime Pattern Learning uses local batch review signals only. It does not post, reply, follow, DM, log in, register accounts, or call external write APIs.",
        }
        self.persist(report)
        return report

    def state(self) -> dict[str, Any]:
        if self.report_path.exists():
            return json.loads(self.report_path.read_text(encoding="utf-8"))
        return self.learn()

    def persist(self, report: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.pattern_memory_path.write_text(json.dumps(report["patternMemory"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.pattern_feed_path.write_text(json.dumps(report["runtimePatternFeed"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.pattern_summary_path.write_text(json.dumps(report["patternLearningSummary"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    @staticmethod
    def _pattern_record(index: int, review: dict[str, Any]) -> dict[str, Any]:
        pattern_type = RuntimePatternLearning._pattern_type(review)
        question_combination = RuntimePatternLearning._question_combination(review)
        return {
            "pattern_id": f"RUNTIME-PATTERN-{index:04d}",
            "source_review_id": review.get("review_id", ""),
            "source_cluster_id": review.get("cluster_id", ""),
            "question_combination": question_combination,
            "cluster_name": review.get("cluster_name", "Unknown cluster"),
            "category": review.get("category", "unknown"),
            "question_count": review.get("question_count", 0),
            "decision": review.get("decision", "unknown"),
            "label": review.get("label", "unknown"),
            "risk_flag": review.get("risk_flag", "watch"),
            "pattern_type": pattern_type,
            "result_pattern": RuntimePatternLearning._result_pattern(pattern_type, review),
            "learning_weight": RuntimePatternLearning._learning_weight(pattern_type, review),
            "recommended_next_action": RuntimePatternLearning._recommended_action(pattern_type, review),
            "created_at": utc_now_iso(),
        }

    @staticmethod
    def _pattern_type(review: dict[str, Any]) -> str:
        label = review.get("label", "")
        decision = review.get("decision", "")
        category = review.get("category", "")
        if decision == "modify":
            return "high_engagement"
        if label in {"spam", "dangerous", "over_marketing"}:
            return "high_risk"
        if label == "high_value":
            return "high_value"
        if category in {"payment_decision", "transport_confusion"} and decision in {"approve", "classify"}:
            return "high_conversion"
        return "high_engagement"

    @staticmethod
    def _question_combination(review: dict[str, Any]) -> str:
        category = review.get("category", "unknown")
        name = review.get("cluster_name", "unknown")
        count = review.get("question_count", 0)
        return f"{category} + {name} + {count} similar questions"

    @staticmethod
    def _result_pattern(pattern_type: str, review: dict[str, Any]) -> str:
        name = review.get("cluster_name", "this cluster")
        if pattern_type == "high_value":
            return f"{name} is a validated high-value cluster and should seed answer branches or content planning."
        if pattern_type == "high_conversion":
            return f"{name} shows decision pressure and may convert when the reply reduces uncertainty."
        if pattern_type == "high_engagement":
            return f"{name} may attract engagement, but needs human-refined angle or stronger evidence."
        return f"{name} contains risk signals and should be blocked or corrected before reuse."

    @staticmethod
    def _learning_weight(pattern_type: str, review: dict[str, Any]) -> float:
        base = {
            "high_value": 0.95,
            "high_conversion": 0.82,
            "high_engagement": 0.68,
            "high_risk": 0.9,
        }[pattern_type]
        question_bonus = min(float(review.get("question_count", 0)) / 100, 0.1)
        return round(min(base + question_bonus, 1.0), 2)

    @staticmethod
    def _recommended_action(pattern_type: str, review: dict[str, Any]) -> str:
        name = review.get("cluster_name", "this cluster")
        if pattern_type == "high_value":
            return f"Promote {name} into best-answer branch generation."
        if pattern_type == "high_conversion":
            return f"Prepare comparison or decision-support reply drafts for {name}."
        if pattern_type == "high_engagement":
            return f"Keep {name} in observation and test a refined hook before scaling."
        return f"Do not train on {name} until the risk is corrected by a human reviewer."

    @staticmethod
    def _summary(pattern_memory: list[dict[str, Any]], reviews: list[dict[str, Any]]) -> dict[str, Any]:
        counts = Counter(item["pattern_type"] for item in pattern_memory)
        return {
            "reviews_learned": len(reviews),
            "patterns_learned": len(pattern_memory),
            "high_value_patterns": counts.get("high_value", 0),
            "high_engagement_patterns": counts.get("high_engagement", 0),
            "high_conversion_patterns": counts.get("high_conversion", 0),
            "high_risk_patterns": counts.get("high_risk", 0),
            "top_pattern": pattern_memory[0]["pattern_type"] if pattern_memory else "none",
            "pattern_memory_ready": bool(pattern_memory),
        }

    @staticmethod
    def _feed(pattern_memory: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "time": item["created_at"],
                "pattern_id": item["pattern_id"],
                "pattern_type": item["pattern_type"],
                "question_combination": item["question_combination"],
                "result_pattern": item["result_pattern"],
                "learning_weight": item["learning_weight"],
                "recommended_next_action": item["recommended_next_action"],
                "risk_flag": item["risk_flag"],
            }
            for item in pattern_memory
        ]


if __name__ == "__main__":
    result = RuntimePatternLearning().learn()
    print(json.dumps({"status": result["status"], "patterns": result["patternLearningSummary"]["patterns_learned"]}, indent=2))
