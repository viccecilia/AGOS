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
from services.intelligence_ranking_noise_filter import IntelligenceRankingNoiseFilter
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
        ranking_dir = root / "intelligence_ranking"

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
        correlation = CrossPlatformCorrelationExpansion(
            platform_profiles_path=platform_dir / "platform_pain_profiles.json",
            market_matrix_path=market_dir / "market_intelligence_matrix.json",
            clusters_path=cluster_dir / "global_pain_clusters.json",
            output_dir=correlation_dir,
        ).build(
            platform["platformPainProfiles"],
            market["marketIntelligenceMatrix"],
            clusters["globalPainClusters"],
        )
        report = IntelligenceRankingNoiseFilter(
            clusters_path=cluster_dir / "global_pain_clusters.json",
            platform_profiles_path=platform_dir / "platform_pain_profiles.json",
            market_matrix_path=market_dir / "market_intelligence_matrix.json",
            correlations_path=correlation_dir / "cross_platform_correlations.json",
            output_dir=ranking_dir,
        ).build(
            clusters["globalPainClusters"],
            platform["platformPainProfiles"],
            market["marketIntelligenceMatrix"],
            correlation["crossPlatformCorrelations"],
        )

        assert report["report_id"] == "INTELLIGENCE_RANKING_REPORT"
        assert report["round_id"] == "ROUND-GLOBAL-006"
        assert report["status"] == "intelligence_ranking_ready"
        ranked = report["rankedIntelligence"]
        assert len(ranked) >= 8

        required_fields = {
            "intelligence_id",
            "source_type",
            "market",
            "platform",
            "pain_cluster",
            "score_breakdown",
            "total_score",
            "ranking_status",
            "noise_reason",
            "recommended_next_step",
            "human_review_required",
        }
        statuses = {item["ranking_status"] for item in ranked}
        assert "high_value" in statuses
        assert {"noise", "low_value"} & statuses
        assert "unsafe" in statuses

        for item in ranked:
            assert required_fields.issubset(item)
            assert item["human_review_required"] is True
            assert item["auto_action_allowed"] is False
            assert item["auto_execute_allowed"] is False
            assert item["auto_publish_allowed"] is False
            assert item["auto_reply_allowed"] is False
            assert item["write_api_allowed"] is False
            for score_name in [
                "pain_strength",
                "frequency",
                "emotion_intensity",
                "market_value",
                "platform_fit",
                "mobility_relevance",
                "conversion_potential",
                "risk_level",
                "evidence_confidence",
            ]:
                assert score_name in item["score_breakdown"], item["intelligence_id"]

        unsafe = report["unsafeSignals"]
        assert unsafe
        assert all(item["unsafe_enters_action"] is False for item in unsafe)
        assert all(item["auto_action_allowed"] is False for item in unsafe)

        summary = report["intelligenceRankingSummary"]
        assert summary["intelligence_ranking_ready"] is True
        assert summary["high_value_count"] >= 1
        assert summary["noise_count"] + summary["low_value_count"] >= 1
        assert summary["unsafe_count"] >= 1
        assert summary["all_items_human_review_required"] is True
        assert summary["auto_action_allowed"] is False
        assert summary["auto_execute_allowed"] is False
        assert summary["auto_publish_allowed"] is False
        assert summary["auto_reply_allowed"] is False
        assert summary["write_api_allowed"] is False
        assert summary["unsafe_enters_action"] is False
        assert summary["noise_enters_action"] is False

        for output_name in [
            "INTELLIGENCE_RANKING_REPORT.json",
            "ranked_intelligence.json",
            "high_value_intelligence.json",
            "noise_filtered_signals.json",
            "unsafe_signals.json",
            "intelligence_ranking_summary.json",
        ]:
            path = ranking_dir / output_name
            assert path.exists(), f"missing output: {output_name}"
            json.loads(path.read_text(encoding="utf-8"))

    print("intelligence_ranking_noise_filter_smoke_test passed")


if __name__ == "__main__":
    main()
