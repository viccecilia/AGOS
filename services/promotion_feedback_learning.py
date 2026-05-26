"""Feedback learning for merchant homepage promotion artifacts."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from services.promotion_review_center import PromotionReviewCenter
from services.runtime_persistence import utc_now_iso


DEFAULT_OUTPUT_DIR = Path("runtime/promotion_feedback_learning")
SUPPORTED_FEEDBACK_TYPES = [
    "posted_manually",
    "liked",
    "replied",
    "saved",
    "shared",
    "ignored",
    "rejected_by_human",
    "modified_by_human",
    "unsafe_flagged",
]


class PromotionFeedbackLearning:
    """Record promotion feedback and learn what should be repeated or avoided."""

    def __init__(self, output_dir: str | Path = DEFAULT_OUTPUT_DIR) -> None:
        self.output_dir = Path(output_dir)
        self.events_path = self.output_dir / "promotion_feedback_events.json"
        self.memory_path = self.output_dir / "promotion_learning_memory.json"
        self.best_path = self.output_dir / "best_promotion_patterns.json"
        self.failed_path = self.output_dir / "failed_promotion_patterns.json"
        self.summary_path = self.output_dir / "promotion_feedback_summary.json"

    def learn(self, feedback_events: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        review_state = PromotionReviewCenter().state()
        events = self._seed_events(review_state)
        if feedback_events:
            events.extend(self._normalize_external_event(item, len(events) + index + 1) for index, item in enumerate(feedback_events))
        memory = self._learning_memory(events)
        best_patterns = self._best_patterns(memory)
        failed_patterns = self._failed_patterns(memory)
        summary = self._summary(events, best_patterns, failed_patterns)
        payload = {
            "report_id": "PROMOTION_FEEDBACK_LEARNING",
            "created_at": utc_now_iso(),
            "status": "promotion_feedback_learning_ready",
            "phase": "MERCHANT_HOMEPAGE_GROWTH_ENGINE",
            "promotionFeedbackEvents": events,
            "promotionLearningMemory": memory,
            "bestPromotionPatterns": best_patterns,
            "failedPromotionPatterns": failed_patterns,
            "promotionFeedbackSummary": summary,
            "supportedFeedbackTypes": SUPPORTED_FEEDBACK_TYPES,
            "safetyBoundary": "Feedback Learning records local/manual/sample feedback only. It does not auto-publish, auto-reply, read private platform data, infer commercial revenue attribution, or execute next actions.",
        }
        self.persist(payload)
        return payload

    def state(self) -> dict[str, Any]:
        if self.summary_path.exists():
            return {
                "report_id": "PROMOTION_FEEDBACK_LEARNING",
                "status": "promotion_feedback_learning_ready",
                "promotionFeedbackEvents": self._read_json(self.events_path, []),
                "promotionLearningMemory": self._read_json(self.memory_path, {}),
                "bestPromotionPatterns": self._read_json(self.best_path, []),
                "failedPromotionPatterns": self._read_json(self.failed_path, []),
                "promotionFeedbackSummary": self._read_json(self.summary_path, {}),
                "supportedFeedbackTypes": SUPPORTED_FEEDBACK_TYPES,
            }
        return self.learn()

    def persist(self, payload: dict[str, Any]) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.events_path.write_text(json.dumps(payload["promotionFeedbackEvents"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.memory_path.write_text(json.dumps(payload["promotionLearningMemory"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.best_path.write_text(json.dumps(payload["bestPromotionPatterns"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.failed_path.write_text(json.dumps(payload["failedPromotionPatterns"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.summary_path.write_text(json.dumps(payload["promotionFeedbackSummary"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    @staticmethod
    def _read_json(path: Path, default: Any) -> Any:
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))

    def _seed_events(self, review_state: dict[str, Any]) -> list[dict[str, Any]]:
        review_items = review_state.get("promotionReviewItems", [])
        decisions = review_state.get("promotionReviewDecisions", [])
        item_by_source = {(item.get("source_type"), item.get("source_id")): item for item in review_items}
        events: list[dict[str, Any]] = []

        high_signal_items = [item for item in review_items if item.get("source_type") == "promotion_plan"][:5]
        positive_types = ["posted_manually", "liked", "replied", "saved", "shared"]
        for index, feedback_type in enumerate(positive_types):
            item = high_signal_items[index % max(len(high_signal_items), 1)] if high_signal_items else {}
            events.append(self._event(len(events) + 1, feedback_type, item, "sample_positive_feedback"))

        ignored_item = next((item for item in review_items if item.get("source_type") == "answer_draft"), review_items[0] if review_items else {})
        events.append(self._event(len(events) + 1, "ignored", ignored_item, "sample_no_engagement"))

        unsafe_item = next((item for item in review_items if item.get("risk_level") == "medium"), review_items[0] if review_items else {})
        events.append(self._event(len(events) + 1, "unsafe_flagged", unsafe_item, "sample_risk_guard"))

        for decision in decisions:
            item = item_by_source.get((decision.get("source_type"), decision.get("source_id")), {})
            if decision.get("human_decision") == "reject":
                events.append(self._event(len(events) + 1, "rejected_by_human", item, decision.get("human_notes", "human rejected")))
            if decision.get("human_decision") == "modify":
                event = self._event(len(events) + 1, "modified_by_human", item, decision.get("human_notes", "human modified"))
                event["modified_version"] = decision.get("modified_version", "")
                events.append(event)
        return events

    def _event(self, index: int, feedback_type: str, item: dict[str, Any], evidence: str) -> dict[str, Any]:
        platform = item.get("platform") or "Reddit"
        item_summary = item.get("item_summary", "")
        return {
            "feedback_id": f"PROMO-FEEDBACK-{index:03d}",
            "feedback_type": feedback_type,
            "source_type": item.get("source_type", "promotion_plan"),
            "source_id": item.get("source_id", item.get("plan_id", "")),
            "workspace_id": item.get("workspace_id", "jag_app_growth"),
            "merchant_name": item.get("merchant_name", "Japan AI Guide App"),
            "platform": platform,
            "market": self._infer_market(item_summary),
            "problem_type": self._infer_problem_type(item_summary),
            "pain_point": self._infer_pain_point(item_summary),
            "answer_style": self._answer_style(item),
            "cta_style": self._cta_style(item, feedback_type),
            "content_format": self._content_format(item),
            "risk_pattern": item.get("risk_level", "low"),
            "evidence": evidence,
            "sample_data_only": True,
            "real_business_result": False,
            "auto_next_action_allowed": False,
            "created_at": utc_now_iso(),
        }

    def _normalize_external_event(self, item: dict[str, Any], index: int) -> dict[str, Any]:
        feedback_type = item.get("feedback_type", "ignored")
        if feedback_type not in SUPPORTED_FEEDBACK_TYPES:
            raise ValueError(f"Unsupported feedback_type: {feedback_type}")
        event = self._event(index, feedback_type, item, item.get("evidence", "manual_feedback"))
        event.update({key: value for key, value in item.items() if key in event or key == "modified_version"})
        event["sample_data_only"] = bool(item.get("sample_data_only", True))
        event["real_business_result"] = False
        event["auto_next_action_allowed"] = False
        return event

    @staticmethod
    def _infer_market(text: str) -> str:
        lowered = text.lower()
        if "china" in lowered or "春节" in text:
            return "China"
        if "us" in lowered or "haneda" in lowered:
            return "US"
        if "taiwan" in lowered:
            return "Taiwan"
        return "Japan"

    @staticmethod
    def _infer_problem_type(text: str) -> str:
        lowered = text.lower()
        if "airport" in lowered or "haneda" in lowered or "narita" in lowered:
            return "airport_transfer"
        if "luggage" in lowered:
            return "luggage_heavy_trip"
        if "family" in lowered or "kids" in lowered:
            return "family_trip"
        if "route" in lowered or "transport" in lowered:
            return "transport_planning"
        return "travel_planning"

    @staticmethod
    def _infer_pain_point(text: str) -> str:
        lowered = text.lower()
        if "luggage" in lowered:
            return "luggage friction"
        if "late" in lowered:
            return "late arrival risk"
        if "family" in lowered or "kids" in lowered:
            return "family travel complexity"
        if "transfer" in lowered:
            return "transfer anxiety"
        return "planning uncertainty"

    @staticmethod
    def _answer_style(item: dict[str, Any]) -> str:
        source_type = item.get("source_type", "")
        if source_type == "answer_draft":
            return "direct_answer_with_steps"
        if source_type == "promotion_plan":
            return "platform_specific_plan"
        return "diagnostic_problem_triage"

    @staticmethod
    def _cta_style(item: dict[str, Any], feedback_type: str = "") -> str:
        cta_risk = item.get("cta_risk", "none")
        if cta_risk == "low":
            if feedback_type in {"posted_manually", "liked", "replied", "saved", "shared"}:
                return "answer_first_soft_reference"
            return "soft_reference"
        if cta_risk == "high":
            return "blocked_cta"
        return "no_cta"

    @staticmethod
    def _content_format(item: dict[str, Any]) -> str:
        summary = item.get("item_summary", "").lower()
        if "short_video" in summary:
            return "short_video_hook"
        if "carousel" in summary:
            return "carousel"
        if "article" in summary:
            return "article"
        return item.get("source_type", "review_item")

    def _learning_memory(self, events: list[dict[str, Any]]) -> dict[str, Any]:
        dimensions = ["problem_type", "pain_point", "platform", "market", "answer_style", "cta_style", "content_format", "risk_pattern"]
        memory: dict[str, Any] = {dimension: [] for dimension in dimensions}
        for dimension in dimensions:
            grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
            for event in events:
                grouped[str(event.get(dimension, "unknown"))].append(event)
            for key, rows in grouped.items():
                memory[dimension].append(
                    {
                        "value": key,
                        "positive_feedback": sum(1 for row in rows if self._is_positive(row)),
                        "failed_feedback": sum(1 for row in rows if self._is_failed(row)),
                        "unsafe_feedback": sum(1 for row in rows if row.get("feedback_type") == "unsafe_flagged"),
                        "sample_data_only": True,
                    }
                )
            memory[dimension] = sorted(memory[dimension], key=lambda row: (-(row["positive_feedback"] - row["failed_feedback"]), row["value"]))
        return memory

    @staticmethod
    def _is_positive(event: dict[str, Any]) -> bool:
        return event.get("feedback_type") in {"posted_manually", "liked", "replied", "saved", "shared"}

    @staticmethod
    def _is_failed(event: dict[str, Any]) -> bool:
        return event.get("feedback_type") in {"ignored", "rejected_by_human", "modified_by_human", "unsafe_flagged"}

    def _best_patterns(self, memory: dict[str, Any]) -> list[dict[str, Any]]:
        patterns = []
        for dimension, rows in memory.items():
            for row in rows:
                if row["positive_feedback"] > 0 and row["unsafe_feedback"] == 0 and row["positive_feedback"] >= row["failed_feedback"]:
                    patterns.append(
                        {
                            "pattern_id": f"BEST-{len(patterns) + 1:03d}",
                            "dimension": dimension,
                            "value": row["value"],
                            "positive_feedback": row["positive_feedback"],
                            "failed_feedback": row["failed_feedback"],
                            "why_best": "Positive sample/manual feedback without unsafe flags.",
                            "sample_data_only": True,
                        }
                    )
        return patterns[:12]

    def _failed_patterns(self, memory: dict[str, Any]) -> list[dict[str, Any]]:
        patterns = []
        for dimension, rows in memory.items():
            for row in rows:
                if row["failed_feedback"] > 0:
                    patterns.append(
                        {
                            "pattern_id": f"FAILED-{len(patterns) + 1:03d}",
                            "dimension": dimension,
                            "value": row["value"],
                            "failed_feedback": row["failed_feedback"],
                            "unsafe_feedback": row["unsafe_feedback"],
                            "why_failed": "Ignored, rejected, modified, or unsafe feedback should be learned as a caution pattern.",
                            "sample_data_only": True,
                        }
                    )
        return patterns[:12]

    @staticmethod
    def _summary(events: list[dict[str, Any]], best_patterns: list[dict[str, Any]], failed_patterns: list[dict[str, Any]]) -> dict[str, Any]:
        feedback_counts = Counter(event["feedback_type"] for event in events)
        best_platforms = [item["value"] for item in best_patterns if item["dimension"] == "platform"][:5]
        best_cta = [item["value"] for item in best_patterns if item["dimension"] == "cta_style"][:3]
        ignored_patterns = [item for item in failed_patterns if item["value"] in {"ignored", "no_cta"} or item["dimension"] in {"risk_pattern", "cta_style"}]
        return {
            "promotion_feedback_learning_ready": True,
            "feedback_event_count": len(events),
            "feedback_type_counts": dict(feedback_counts),
            "feedback_types_observed": sorted(feedback_counts),
            "best_pattern_count": len(best_patterns),
            "failed_pattern_count": len(failed_patterns),
            "best_problem_types": [item["value"] for item in best_patterns if item["dimension"] == "problem_type"][:5],
            "best_platforms": best_platforms,
            "best_cta": best_cta,
            "ignored_patterns": ignored_patterns[:5],
            "rejected_patterns": [item for item in failed_patterns if item["failed_feedback"] > 0][:5],
            "unsafe_patterns": [item for item in failed_patterns if item["unsafe_feedback"] > 0],
            "unsafe_in_best_patterns": any(item["value"] == "unsafe_flagged" for item in best_patterns),
            "next_recommendation": "Prioritize soft-reference CTA on practical transport planning problems for Reddit/SEO/Xiaohongshu, and avoid patterns that were rejected, modified for softer CTA, ignored, or unsafe flagged.",
            "sample_data_only": True,
            "real_business_result": False,
            "auto_next_action_allowed": False,
        }


if __name__ == "__main__":
    result = PromotionFeedbackLearning().learn()
    print(json.dumps({"status": result["status"], "summary": result["promotionFeedbackSummary"]}, indent=2))
