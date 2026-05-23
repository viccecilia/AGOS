from __future__ import annotations

import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.batch_scout_runtime import BatchScoutRuntime
from services.batch_topic_clustering import BatchTopicClustering


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        runtime_report = BatchScoutRuntime(Path(tmp) / "batch_runtime").run(
            BatchScoutRuntime.generate_sample_questions(100)
        )
        cluster_root = Path(tmp) / "batch_clusters"
        report = BatchTopicClustering(cluster_root).cluster(runtime_report["batchAnalysis"])

        assert report["report_id"] == "BATCH_TOPIC_CLUSTERING_REPORT"
        assert report["status"] == "batch_clusters_ready"
        assert report["scope"] == "local_batch_topic_clustering"
        assert {"similar_questions", "frequent_questions", "high_emotion_questions", "high_growth_signals"}.issubset(
            set(report["clusterDimensions"])
        )

        summary = report["batchClusterSummary"]
        assert summary["questions_clustered"] == 100
        assert summary["clusters_created"] >= 4
        assert summary["high_frequency_clusters"] >= 4
        assert summary["high_emotion_clusters"] >= 3
        assert summary["high_growth_signal_clusters"] >= 1
        assert summary["batch_clustering_ready"] is True

        clusters = report["batchTrendClusters"]
        assert clusters[0]["rank"] == 1
        assert clusters[0]["growth_signal_score"] >= clusters[-1]["growth_signal_score"]
        assert any(item["cluster_name"] == "Tokyo transport anxiety" for item in clusters)
        assert any(item["high_growth_signal"] for item in clusters)

        for item in clusters:
            assert item["frequency"] > 0
            assert item["similar_question_count"] == item["frequency"]
            assert item["sample_questions"]
            assert item["source_question_ids"]
            assert item["recommended_cluster_action"]
            assert item["status"] == "clustered"

        assert report["batchClusterFeed"], "batch cluster feed is required"
        assert (cluster_root / "BATCH_TOPIC_CLUSTERING_REPORT.json").exists()
        assert (cluster_root / "batch_trend_clusters.json").exists()
        assert (cluster_root / "batch_cluster_feed.json").exists()
        assert (cluster_root / "batch_cluster_summary.json").exists()

    print("batch topic clustering smoke test passed")


if __name__ == "__main__":
    main()
