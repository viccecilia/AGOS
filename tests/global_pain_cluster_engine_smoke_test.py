from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.global_batch_intelligence_collection import GlobalBatchIntelligenceCollection
from services.global_pain_cluster_engine import GlobalPainClusterEngine


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        batch_dir = root / "global_batch_intelligence_collection"
        cluster_dir = root / "global_pain_clusters"
        batch = GlobalBatchIntelligenceCollection(batch_dir).collect()
        report = GlobalPainClusterEngine(
            input_path=batch_dir / "global_intelligence_records.json",
            output_dir=cluster_dir,
        ).build()

        assert report["report_id"] == "GLOBAL_PAIN_CLUSTER_REPORT"
        assert report["round_id"] == "ROUND-GLOBAL-002"
        assert report["status"] == "global_pain_clusters_ready"
        clusters = report["globalPainClusters"]
        assert len(clusters) >= 5
        assert len(batch["globalIntelligenceRecords"]) >= 20

        required_fields = {
            "cluster_id",
            "cluster_name",
            "markets",
            "platforms",
            "languages",
            "source_record_ids",
            "pain_points",
            "emotion_tags",
            "frequency_score",
            "emotion_intensity_score",
            "business_relevance_score",
            "human_review_required",
        }
        for cluster in clusters:
            assert required_fields.issubset(cluster)
            assert cluster["source_record_ids"], cluster["cluster_id"]
            assert cluster["frequency_score"] > 0
            assert cluster["emotion_intensity_score"] > 0
            assert cluster["business_relevance_score"] > 0
            assert cluster["human_review_required"] is True
            assert cluster["auto_reply_allowed"] is False
            assert cluster["reply_generation_allowed"] is False
            assert cluster["promotion_allowed"] is False

        summary = report["globalPainClusterSummary"]
        assert summary["global_pain_cluster_ready"] is True
        assert summary["input_record_count"] >= 20
        assert summary["cluster_count"] >= 5
        assert summary["cross_market_cluster_count"] >= 1
        assert summary["cross_platform_cluster_count"] >= 1
        assert summary["ranking_candidate_count"] >= 1
        assert summary["all_clusters_need_human_review"] is True
        assert summary["auto_reply_allowed"] is False
        assert summary["reply_generation_allowed"] is False
        assert summary["promotion_allowed"] is False

        for output_name in [
            "GLOBAL_PAIN_CLUSTER_REPORT.json",
            "global_pain_clusters.json",
            "pain_cluster_sources.json",
            "pain_cluster_feed.json",
            "global_pain_cluster_summary.json",
        ]:
            path = cluster_dir / output_name
            assert path.exists(), f"missing output: {output_name}"
            json.loads(path.read_text(encoding="utf-8"))

    print("global_pain_cluster_engine_smoke_test passed")


if __name__ == "__main__":
    main()
