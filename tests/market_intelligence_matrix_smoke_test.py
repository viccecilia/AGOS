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
from services.market_intelligence_matrix import MarketIntelligenceMatrix
from services.platform_pain_intelligence import PlatformPainIntelligence


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        batch_dir = root / "global_batch_intelligence_collection"
        cluster_dir = root / "global_pain_clusters"
        platform_dir = root / "platform_pain_intelligence"
        market_dir = root / "market_intelligence_matrix"

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
        report = MarketIntelligenceMatrix(
            records_path=batch_dir / "global_intelligence_records.json",
            clusters_path=cluster_dir / "global_pain_clusters.json",
            platform_profiles_path=platform_dir / "platform_pain_profiles.json",
            output_dir=market_dir,
        ).build(
            batch["globalIntelligenceRecords"],
            clusters["globalPainClusters"],
            platform["platformPainProfiles"],
        )

        assert report["report_id"] == "MARKET_INTELLIGENCE_MATRIX_REPORT"
        assert report["round_id"] == "ROUND-GLOBAL-004"
        assert report["status"] == "market_intelligence_matrix_ready"
        matrix = report["marketIntelligenceMatrix"]
        assert len(matrix) >= 5

        required_fields = {
            "market",
            "languages",
            "dominant_pain_points",
            "travel_style",
            "mobility_need",
            "trust_barrier",
            "price_sensitivity",
            "platform_preference",
            "content_tone",
            "conversion_risk",
            "opportunity_score",
        }
        by_market = {item["market"]: item for item in matrix}
        for item in matrix:
            assert required_fields.issubset(item)
            assert item["platform_preference"], item["market"]
            assert item["opportunity_score"] > 0
            assert item["human_review_required"] is True
            assert item["auto_promotion_allowed"] is False
            assert item["auto_reply_allowed"] is False
            assert item["write_api_allowed"] is False

        assert "China outbound" in by_market
        assert "Japan" in by_market
        assert by_market["China outbound"]["market_isolation_key"] == "China outbound"
        assert by_market["Japan"]["market_isolation_key"] == "Japan"
        assert by_market["China outbound"]["market_isolation_key"] != by_market["Japan"]["market_isolation_key"]
        assert any(pref["platform"] == "Xiaohongshu" for pref in by_market["China outbound"]["platform_preference"])

        summary = report["marketIntelligenceSummary"]
        assert summary["market_intelligence_matrix_ready"] is True
        assert summary["market_count"] >= 5
        assert summary["all_markets_human_review_required"] is True
        assert summary["auto_promotion_allowed"] is False
        assert summary["auto_reply_allowed"] is False
        assert summary["write_api_allowed"] is False
        assert summary["china_outbound_pollutes_japan_local"] is False

        assert report["marketPlatformFit"]
        assert report["marketPainRanking"]

        for output_name in [
            "MARKET_INTELLIGENCE_MATRIX_REPORT.json",
            "market_intelligence_matrix.json",
            "market_platform_fit.json",
            "market_pain_ranking.json",
            "market_intelligence_summary.json",
        ]:
            path = market_dir / output_name
            assert path.exists(), f"missing output: {output_name}"
            json.loads(path.read_text(encoding="utf-8"))

    print("market_intelligence_matrix_smoke_test passed")


if __name__ == "__main__":
    main()
