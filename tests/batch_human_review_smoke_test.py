from pathlib import Path
from tempfile import TemporaryDirectory
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.batch_human_review import BatchHumanReview, SUPPORTED_DECISIONS, SUPPORTED_LABELS
from services.batch_scout_runtime import BatchScoutRuntime
from services.batch_topic_clustering import BatchTopicClustering


def test_batch_human_review_supports_bulk_decisions_and_labels() -> None:
    with TemporaryDirectory() as tmp:
        base = Path(tmp)
        scout = BatchScoutRuntime(base / "batch_runtime").run()
        clusters = BatchTopicClustering(base / "batch_clusters").cluster(scout["batchAnalysis"])
        review = BatchHumanReview(base / "batch_reviews").review(clusters["batchTrendClusters"])

        summary = review["batchHumanReviewSummary"]
        decisions = {item["decision"] for item in review["batchReviewQueue"]}
        labels = {item["label"] for item in review["batchReviewQueue"]}

        assert review["status"] == "batch_human_review_ready"
        assert review["supportedDecisions"] == SUPPORTED_DECISIONS
        assert review["supportedLabels"] == SUPPORTED_LABELS
        assert summary["review_items"] == clusters["batchClusterSummary"]["clusters_created"]
        assert {"approve", "reject", "modify", "classify"}.issubset(decisions)
        assert {"high_value", "low_value", "spam", "dangerous", "over_marketing"}.issubset(labels)
        assert summary["batch_training_ready"] is True
        assert summary["human_gate_required"] is True
        assert any(item["human_modified_cluster_name"] for item in review["batchReviewQueue"])
        assert all(item["human_gate_status"] == "completed" for item in review["batchReviewQueue"])

        assert (base / "batch_reviews" / "BATCH_HUMAN_REVIEW_REPORT.json").exists()
        assert (base / "batch_reviews" / "batch_review_queue.json").exists()
        assert (base / "batch_reviews" / "batch_review_decisions.json").exists()
        assert (base / "batch_reviews" / "batch_training_labels.json").exists()
        assert (base / "batch_reviews" / "batch_review_feed.json").exists()


if __name__ == "__main__":
    test_batch_human_review_supports_bulk_decisions_and_labels()
    print("batch_human_review_smoke_test passed")
