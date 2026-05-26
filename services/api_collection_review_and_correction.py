"""Review and correct collected API intelligence before it trains AGOS memory."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.live_data_import_to_memory import LiveDataImportToMemory
from services.runtime_persistence import utc_now_iso


SUPPORTED_ACTIONS = [
    "approve",
    "reject",
    "classify",
    "mark_low_value",
    "mark_high_value",
]

CORRECTION_FIELDS = [
    "pain_points",
    "emotion_tags",
    "trend_strength",
    "source_confidence",
]


class APICollectionReviewAndCorrection:
    """Batch-review and correct live intelligence collection outputs."""

    def __init__(self, root: str | Path = "runtime/api_collection_review") -> None:
        self.root = Path(root)
        self.report_path = self.root / "API_COLLECTION_REVIEW_AND_CORRECTION_REPORT.json"
        self.review_queue_path = self.root / "collection_review_queue.json"
        self.decisions_path = self.root / "collection_review_decisions.json"
        self.corrected_path = self.root / "corrected_collection_intelligence.json"
        self.feed_path = self.root / "collection_correction_feed.json"
        self.summary_path = self.root / "collection_review_summary.json"

    def review(
        self,
        live_memory_import: dict[str, Any] | None = None,
        decisions: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        source = live_memory_import if live_memory_import is not None else LiveDataImportToMemory().state()
        review_queue = self._build_review_queue(source)
        review_decisions = self._resolve_decisions(review_queue, decisions)
        corrected_intelligence = self._apply_decisions(review_queue, review_decisions)
        correction_feed = self._feed(review_queue, review_decisions, corrected_intelligence)
        summary = self._summary(review_queue, review_decisions, corrected_intelligence)
        report = {
            "report_id": "API_COLLECTION_REVIEW_AND_CORRECTION_REPORT",
            "created_at": utc_now_iso(),
            "status": "api_collection_review_ready",
            "scope": "controlled_api_intelligence_collection",
            "supportedActions": SUPPORTED_ACTIONS,
            "correctionFields": CORRECTION_FIELDS,
            "collectionReviewQueue": review_queue,
            "collectionReviewDecisions": review_decisions,
            "correctedCollectionIntelligence": corrected_intelligence,
            "collectionCorrectionFeed": correction_feed,
            "collectionReviewSummary": summary,
            "safetyBoundary": "API Collection Review and Correction edits local intelligence records only. It does not post, reply, follow, DM, log in, register accounts, call platform write APIs, or bypass platform limits.",
        }
        self.persist(report)
        return report

    def state(self) -> dict[str, Any]:
        if self.report_path.exists():
            return json.loads(self.report_path.read_text(encoding="utf-8"))
        return self.review()

    def persist(self, report: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.review_queue_path.write_text(json.dumps(report["collectionReviewQueue"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.decisions_path.write_text(json.dumps(report["collectionReviewDecisions"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.corrected_path.write_text(json.dumps(report["correctedCollectionIntelligence"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.feed_path.write_text(json.dumps(report["collectionCorrectionFeed"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.summary_path.write_text(json.dumps(report["collectionReviewSummary"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    @staticmethod
    def _build_review_queue(source: dict[str, Any]) -> list[dict[str, Any]]:
        questions = source.get("questionInboxMemory", [])
        scouts = {
            item.get("source_url", ""): item
            for item in source.get("scoutIntelligenceMemory", [])
        }
        clusters = source.get("trendClusterMemory", [])
        queue = []
        for index, question in enumerate(questions, start=1):
            source_url = question.get("source_url", "")
            scout = scouts.get(source_url, {})
            matched_clusters = [
                cluster
                for cluster in clusters
                if question.get("source_normalized_id", "") in cluster.get("source_items", [])
            ]
            queue.append(
                {
                    "review_id": f"API-COLLECT-REVIEW-{index:04d}",
                    "source_question_id": question.get("question_id", ""),
                    "source_normalized_id": question.get("source_normalized_id", ""),
                    "platform": question.get("platform", "unknown"),
                    "market": question.get("market", "global"),
                    "language": question.get("language", "unknown"),
                    "source_url": source_url,
                    "question_text": question.get("question_text", ""),
                    "current_pain_points": question.get("pain_points", []),
                    "current_emotion_tags": question.get("emotion_tags", []),
                    "current_trend_strength": scout.get("training_value_score", question.get("priority_score", 0)),
                    "current_source_confidence": scout.get("source_confidence", 0),
                    "matched_trend_clusters": [cluster.get("cluster_id", "") for cluster in matched_clusters],
                    "suggested_action": APICollectionReviewAndCorrection._suggested_action(question, scout),
                    "review_status": "needs_human_review",
                    "created_at": utc_now_iso(),
                }
            )
        return queue

    @staticmethod
    def _suggested_action(question: dict[str, Any], scout: dict[str, Any]) -> str:
        score = int(question.get("priority_score", scout.get("training_value_score", 0)))
        confidence = float(scout.get("source_confidence", 0))
        if score >= 90 and confidence >= 0.75:
            return "mark_high_value"
        if score < 55 or confidence < 0.55:
            return "mark_low_value"
        return "classify"

    @staticmethod
    def _resolve_decisions(
        review_queue: list[dict[str, Any]],
        decisions: list[dict[str, Any]] | None,
    ) -> list[dict[str, Any]]:
        by_id = {item.get("review_id"): item for item in decisions or []}
        resolved = []
        for item in review_queue:
            provided = by_id.get(item["review_id"], {})
            action = provided.get("action", item.get("suggested_action", "classify"))
            if action not in SUPPORTED_ACTIONS:
                action = "classify"
            corrections = provided.get("corrections", {})
            resolved.append(
                {
                    "decision_id": f"API-COLLECT-DECISION-{len(resolved) + 1:04d}",
                    "review_id": item["review_id"],
                    "action": action,
                    "corrections": APICollectionReviewAndCorrection._validated_corrections(corrections),
                    "reason": provided.get("reason", APICollectionReviewAndCorrection._default_reason(action, item)),
                    "decided_by": provided.get("decided_by", "AGOS local review rule"),
                    "decided_at": utc_now_iso(),
                }
            )
        return resolved

    @staticmethod
    def _validated_corrections(corrections: dict[str, Any]) -> dict[str, Any]:
        validated = {}
        for key in CORRECTION_FIELDS:
            if key not in corrections:
                continue
            value = corrections[key]
            if key in {"pain_points", "emotion_tags"}:
                validated[key] = [str(item) for item in value] if isinstance(value, list) else [str(value)]
            elif key == "trend_strength":
                validated[key] = max(0, min(100, int(value)))
            elif key == "source_confidence":
                validated[key] = round(max(0.0, min(1.0, float(value))), 3)
        return validated

    @staticmethod
    def _default_reason(action: str, item: dict[str, Any]) -> str:
        if action == "approve":
            return "Signal is acceptable for local training memory."
        if action == "reject":
            return "Signal is not reliable enough for training memory."
        if action == "mark_high_value":
            return "Signal has strong priority and confidence for controlled training."
        if action == "mark_low_value":
            return "Signal is weak or needs more evidence before training."
        return f"Classify {item.get('source_question_id', '')} for corrected intelligence routing."

    @staticmethod
    def _apply_decisions(
        review_queue: list[dict[str, Any]],
        decisions: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        by_id = {item["review_id"]: item for item in decisions}
        corrected = []
        for item in review_queue:
            decision = by_id[item["review_id"]]
            corrections = decision.get("corrections", {})
            action = decision["action"]
            corrected.append(
                {
                    "corrected_id": f"API-COLLECT-CORRECTED-{len(corrected) + 1:04d}",
                    "review_id": item["review_id"],
                    "source_question_id": item.get("source_question_id", ""),
                    "platform": item.get("platform", "unknown"),
                    "market": item.get("market", "global"),
                    "language": item.get("language", "unknown"),
                    "source_url": item.get("source_url", ""),
                    "question_text": item.get("question_text", ""),
                    "pain_points": corrections.get("pain_points", item.get("current_pain_points", [])),
                    "emotion_tags": corrections.get("emotion_tags", item.get("current_emotion_tags", [])),
                    "trend_strength": corrections.get("trend_strength", item.get("current_trend_strength", 0)),
                    "source_confidence": corrections.get("source_confidence", item.get("current_source_confidence", 0)),
                    "review_action": action,
                    "training_route": APICollectionReviewAndCorrection._training_route(action),
                    "human_review_required": action in {"reject", "mark_low_value"} or bool(corrections),
                    "corrected_at": utc_now_iso(),
                }
            )
        return corrected

    @staticmethod
    def _training_route(action: str) -> str:
        if action in {"approve", "mark_high_value"}:
            return "approved_training_memory"
        if action == "reject":
            return "blocked_from_training"
        if action == "mark_low_value":
            return "watchlist_low_value"
        return "classified_training_memory"

    @staticmethod
    def _feed(
        review_queue: list[dict[str, Any]],
        decisions: list[dict[str, Any]],
        corrected: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        corrected_by_review = {item["review_id"]: item for item in corrected}
        feed = []
        for decision in decisions:
            corrected_item = corrected_by_review[decision["review_id"]]
            changed_fields = sorted(decision.get("corrections", {}).keys())
            feed.append(
                {
                    "time": decision["decided_at"],
                    "review_id": decision["review_id"],
                    "action": decision["action"],
                    "platform": corrected_item.get("platform", "unknown"),
                    "source_question_id": corrected_item.get("source_question_id", ""),
                    "correction_type": changed_fields or ["review_action"],
                    "correction_reason": decision["reason"],
                    "training_route": corrected_item["training_route"],
                    "human_review_required": corrected_item["human_review_required"],
                }
            )
        return feed

    @staticmethod
    def _summary(
        review_queue: list[dict[str, Any]],
        decisions: list[dict[str, Any]],
        corrected: list[dict[str, Any]],
    ) -> dict[str, Any]:
        actions = [item["action"] for item in decisions]
        corrected_fields = [field for item in decisions for field in item.get("corrections", {}).keys()]
        return {
            "review_ready": bool(review_queue),
            "review_items": len(review_queue),
            "approved": actions.count("approve"),
            "rejected": actions.count("reject"),
            "classified": actions.count("classify"),
            "marked_low_value": actions.count("mark_low_value"),
            "marked_high_value": actions.count("mark_high_value"),
            "corrected_records": len([item for item in decisions if item.get("corrections")]),
            "pain_point_corrections": corrected_fields.count("pain_points"),
            "emotion_corrections": corrected_fields.count("emotion_tags"),
            "trend_corrections": corrected_fields.count("trend_strength"),
            "source_confidence_corrections": corrected_fields.count("source_confidence"),
            "approved_training_memory": len([item for item in corrected if item["training_route"] == "approved_training_memory"]),
            "blocked_from_training": len([item for item in corrected if item["training_route"] == "blocked_from_training"]),
            "write_operations_enabled": False,
        }


if __name__ == "__main__":
    result = APICollectionReviewAndCorrection().review()
    print(json.dumps({"status": result["status"], "summary": result["collectionReviewSummary"]}, indent=2))
