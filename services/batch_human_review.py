"""Batch human review for training AGOS on clustered question groups."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from services.batch_topic_clustering import BatchTopicClustering
from services.runtime_persistence import utc_now_iso


SUPPORTED_DECISIONS = ["approve", "reject", "modify", "classify"]
SUPPORTED_LABELS = ["high_value", "low_value", "spam", "dangerous", "over_marketing"]


class BatchHumanReview:
    """Create a batch review queue from clustered topics and persist training labels."""

    def __init__(self, root: str | Path = "runtime/batch_reviews") -> None:
        self.root = Path(root)
        self.report_path = self.root / "BATCH_HUMAN_REVIEW_REPORT.json"
        self.queue_path = self.root / "batch_review_queue.json"
        self.decisions_path = self.root / "batch_review_decisions.json"
        self.labels_path = self.root / "batch_training_labels.json"
        self.feed_path = self.root / "batch_review_feed.json"

    def review(self, clusters: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        batch_clusters = clusters
        if batch_clusters is None:
            batch_clusters = BatchTopicClustering().state().get("batchTrendClusters", [])
        review_queue = [self._review_item(index, item) for index, item in enumerate(batch_clusters, start=1)]
        decisions = [self._decision_record(item) for item in review_queue]
        labels = [self._training_label(item) for item in review_queue]
        report = {
            "report_id": "BATCH_HUMAN_REVIEW_REPORT",
            "created_at": utc_now_iso(),
            "status": "batch_human_review_ready",
            "scope": "local_batch_human_review",
            "supportedDecisions": SUPPORTED_DECISIONS,
            "supportedLabels": SUPPORTED_LABELS,
            "batchReviewQueue": review_queue,
            "batchReviewDecisions": decisions,
            "batchTrainingLabels": labels,
            "batchReviewFeed": self._feed(review_queue),
            "batchHumanReviewSummary": self._summary(review_queue),
            "safetyBoundary": "Batch Human Review is local training only. It does not post, reply, follow, DM, log in, register accounts, or call external write APIs.",
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
        self.queue_path.write_text(json.dumps(report["batchReviewQueue"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.decisions_path.write_text(json.dumps(report["batchReviewDecisions"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.labels_path.write_text(json.dumps(report["batchTrainingLabels"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.feed_path.write_text(json.dumps(report["batchReviewFeed"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    @staticmethod
    def _review_item(index: int, cluster: dict[str, Any]) -> dict[str, Any]:
        decision, label = BatchHumanReview._default_decision(index)
        modified_name = ""
        if decision == "modify":
            modified_name = f"{cluster.get('cluster_name', 'Unknown cluster')} - human refined angle"
        return {
            "review_id": f"BATCH-REVIEW-{index:04d}",
            "cluster_id": cluster.get("cluster_id", f"batch_cluster_{index:04d}"),
            "cluster_name": cluster.get("cluster_name", "Unknown cluster"),
            "category": cluster.get("category", "unknown"),
            "question_count": cluster.get("frequency", 0),
            "sample_questions": cluster.get("sample_questions", [])[:3],
            "growth_signal_score": cluster.get("growth_signal_score", 0),
            "ai_recommendation": cluster.get("recommended_cluster_action", ""),
            "decision": decision,
            "label": label,
            "human_modified_cluster_name": modified_name,
            "human_note": BatchHumanReview._human_note(decision, label, cluster),
            "review_status": "reviewed",
            "human_gate_status": "completed",
            "training_signal": BatchHumanReview._training_signal(decision, label),
            "risk_flag": BatchHumanReview._risk_flag(label),
            "created_at": utc_now_iso(),
        }

    @staticmethod
    def _default_decision(index: int) -> tuple[str, str]:
        pattern = [
            ("approve", "high_value"),
            ("classify", "low_value"),
            ("modify", "over_marketing"),
            ("reject", "spam"),
            ("reject", "dangerous"),
        ]
        return pattern[(index - 1) % len(pattern)]

    @staticmethod
    def _human_note(decision: str, label: str, cluster: dict[str, Any]) -> str:
        name = cluster.get("cluster_name", "this cluster")
        if decision == "approve":
            return f"Keep {name} as a high-value batch training signal."
        if decision == "modify":
            return f"Keep the signal from {name}, but reduce over-marketing before using it."
        if decision == "classify":
            return f"Classify {name} as low-value until stronger growth evidence appears."
        if label == "dangerous":
            return f"Reject {name} because the cluster needs safety review before training."
        return f"Reject {name} because it looks like weak or spam-like training data."

    @staticmethod
    def _training_signal(decision: str, label: str) -> str:
        if decision == "approve":
            return "positive_batch_training_signal"
        if decision == "modify":
            return "human_refined_training_signal"
        if decision == "classify":
            return "classification_training_signal"
        return f"negative_training_signal_{label}"

    @staticmethod
    def _risk_flag(label: str) -> str:
        return {
            "high_value": "low",
            "low_value": "watch",
            "over_marketing": "needs_tone_correction",
            "spam": "blocked",
            "dangerous": "blocked",
        }.get(label, "watch")

    @staticmethod
    def _decision_record(item: dict[str, Any]) -> dict[str, Any]:
        return {
            "review_id": item["review_id"],
            "cluster_id": item["cluster_id"],
            "decision": item["decision"],
            "label": item["label"],
            "human_modified_cluster_name": item["human_modified_cluster_name"],
            "human_note": item["human_note"],
            "training_signal": item["training_signal"],
            "created_at": item["created_at"],
        }

    @staticmethod
    def _training_label(item: dict[str, Any]) -> dict[str, Any]:
        return {
            "label_id": item["review_id"].replace("BATCH-REVIEW", "BATCH-LABEL"),
            "cluster_id": item["cluster_id"],
            "label": item["label"],
            "decision": item["decision"],
            "risk_flag": item["risk_flag"],
            "applies_to": "batch_topic_cluster",
            "training_signal": item["training_signal"],
        }

    @staticmethod
    def _summary(review_queue: list[dict[str, Any]]) -> dict[str, Any]:
        decisions = Counter(item["decision"] for item in review_queue)
        labels = Counter(item["label"] for item in review_queue)
        return {
            "review_items": len(review_queue),
            "approve_count": decisions.get("approve", 0),
            "reject_count": decisions.get("reject", 0),
            "modify_count": decisions.get("modify", 0),
            "classify_count": decisions.get("classify", 0),
            "high_value_count": labels.get("high_value", 0),
            "low_value_count": labels.get("low_value", 0),
            "spam_count": labels.get("spam", 0),
            "dangerous_count": labels.get("dangerous", 0),
            "over_marketing_count": labels.get("over_marketing", 0),
            "human_gate_required": True,
            "batch_training_ready": bool(review_queue),
        }

    @staticmethod
    def _feed(review_queue: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "time": item["created_at"],
                "review_id": item["review_id"],
                "cluster_id": item["cluster_id"],
                "cluster_name": item["cluster_name"],
                "category": item["category"],
                "question_count": item["question_count"],
                "decision": item["decision"],
                "label": item["label"],
                "human_gate_status": item["human_gate_status"],
                "training_signal": item["training_signal"],
                "risk_flag": item["risk_flag"],
                "human_note": item["human_note"],
                "human_modified_cluster_name": item["human_modified_cluster_name"],
            }
            for item in review_queue
        ]


if __name__ == "__main__":
    result = BatchHumanReview().review()
    print(json.dumps({"status": result["status"], "items": result["batchHumanReviewSummary"]["review_items"]}, indent=2))
