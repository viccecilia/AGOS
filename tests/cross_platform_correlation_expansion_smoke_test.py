from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.cross_platform_correlation_expansion import CrossPlatformCorrelationExpansion
from services.global_batch_intelligence_collection import GlobalBatchIntelligenceCollection
from services.global_pain_cluster_engine import GlobalPainClusterEngine
from services.market_intelligence_matrix import MarketIntelligenceMatrix
from services.platform_pain_intelligence import PlatformPainIntelligence


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        batch_dir = root / "global_batch_intelligence_collection"
        cluster_dir = root / "global_pain_clusters"
        platform_dir = root / "platform_pain_intelligence"
        market_dir = root / "market_intelligence_matrix"
        correlation_dir = root / "cross_platform_correlation"

        batch = GlobalBatchIntelligenceCollection(batch_dir).collect()
        clusters = GlobalPainClusterEngine(
            input_path=batch_dir / "global_intelligence_records.json",
            output_dir=cluster_dir,
        ).build()
        platform = PlatformPainIntelligence(
            clusters_path=cluster_dir / "global_pain_clusters.json",
            records_path=batch_dir / "global_intelligence_records.json",
            output_dir=platform_dir,
        ).build(clusters["globalPainClusters"], batch["globalIntelligenceRecords"])
        market = MarketIntelligenceMatrix(
            records_path=batch_dir / "global_intelligence_records.json",
            clusters_path=cluster_dir / "global_pain_clusters.json",
            platform_profiles_path=platform_dir / "platform_pain_profiles.json",
            output_dir=market_dir,
        ).build(
            batch["globalIntelligenceRecords"],
            clusters["globalPainClusters"],
            platform["platformPainProfiles"],
        )
        report = CrossPlatformCorrelationExpansion(
            platform_profiles_path=platform_dir / "platform_pain_profiles.json",
            market_matrix_path=market_dir / "market_intelligence_matrix.json",
            clusters_path=cluster_dir / "global_pain_clusters.json",
            output_dir=correlation_dir,
        ).build(
            platform["platformPainProfiles"],
            market["marketIntelligenceMatrix"],
            clusters["globalPainClusters"],
        )

        assert report["report_id"] == "CROSS_PLATFORM_CORRELATION_REPORT"
        assert report["round_id"] == "ROUND-GLOBAL-005"
        assert report["status"] == "cross_platform_correlation_ready"
        correlations = report["crossPlatformCorrelations"]
        assert len(correlations) >= 5

        required_fields = {
            "correlation_id",
            "source_platform",
            "target_platforms",
            "source_pain",
            "market",
            "why_correlated",
            "content_expansion_fit",
            "risk_level",
            "human_review_required",
            "auto_publish_allowed",
        }
        for item in correlations:
            assert required_fields.issubset(item)
            assert item["source_platform"]
            assert item["target_platforms"]
            assert item["human_review_required"] is True
            assert item["auto_publish_allowed"] is False
            assert item["auto_reply_allowed"] is False
            assert item["publish_task_created"] is False
            assert item["write_api_allowed"] is False

        reddit = next(item for item in correlations if item["source_platform"] == "Reddit")
        assert "TikTok" in reddit["target_platforms"]
        tiktok = next(item for item in correlations if item["source_platform"] == "TikTok")
        assert "SEO / Search" in tiktok["target_platforms"]
        youtube = next(item for item in correlations if item["source_platform"] == "YouTube")
        assert "X" in youtube["target_platforms"]
        xhs = next(item for item in correlations if item["source_platform"] == "Xiaohongshu")
        assert "Instagram" in xhs["target_platforms"]

        risk = report["correlationRiskReview"]
        assert risk["all_correlations_human_review_required"] is True
        assert risk["auto_publish_allowed"] is False
        assert risk["auto_reply_allowed"] is False
        assert risk["publish_task_created"] is False
        assert risk["write_api_allowed"] is False
        assert risk["high_risk_correlation_count"] >= 1

        summary = report["crossPlatformCorrelationSummary"]
        assert summary["cross_platform_correlation_ready"] is True
        assert summary["correlation_count"] >= 5
        assert summary["source_platform_count"] >= 5
        assert summary["target_platform_count"] >= 5
        assert summary["all_correlations_human_review_required"] is True
        assert summary["auto_publish_allowed"] is False
        assert summary["auto_reply_allowed"] is False
        assert summary["publish_task_created"] is False
        assert summary["write_api_allowed"] is False

        for output_name in [
            "CROSS_PLATFORM_CORRELATION_REPORT.json",
            "cross_platform_correlations.json",
            "platform_expansion_map.json",
            "correlation_risk_review.json",
            "cross_platform_correlation_summary.json",
        ]:
            path = correlation_dir / output_name
            assert path.exists(), f"missing output: {output_name}"
            json.loads(path.read_text(encoding="utf-8"))

    print("cross_platform_correlation_expansion_smoke_test passed")


if __name__ == "__main__":
    main()
