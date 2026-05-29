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
from services.seasonal_demand_calendar_engine import SeasonalDemandCalendarEngine
from services.seasonal_intelligence_engine import SeasonalIntelligenceEngine
from services.seasonal_trend_import_trial import SeasonalTrendImportTrial


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        calendar_dir = root / "seasonal_demand_calendar"
        trend_dir = root / "seasonal_trend_import_trial"
        sample_dir = root / "import_samples"
        batch_dir = root / "global_batch_intelligence_collection"
        cluster_dir = root / "global_pain_clusters"
        platform_dir = root / "platform_pain_intelligence"
        market_dir = root / "market_intelligence_matrix"
        correlation_dir = root / "cross_platform_correlation"
        ranking_dir = root / "intelligence_ranking"
        seasonal_intel_dir = root / "seasonal_intelligence"

        calendar = SeasonalDemandCalendarEngine(calendar_dir).build()
        sample_dir.mkdir(parents=True, exist_ok=True)
        sample_csv = PROJECT_ROOT / "runtime" / "seasonal_demand_calendar" / "import_samples" / "google_trends_japan_travel_sample.csv"
        (sample_dir / "google_trends_japan_travel_sample.csv").write_text(sample_csv.read_text(encoding="utf-8"), encoding="utf-8")
        trend = SeasonalTrendImportTrial(sample_dir=sample_dir, output_dir=trend_dir).run()

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
        ranking = IntelligenceRankingNoiseFilter(
            clusters_path=cluster_dir / "global_pain_clusters.json",
            platform_profiles_path=platform_dir / "platform_pain_intelligence.json",
            market_matrix_path=market_dir / "market_intelligence_matrix.json",
            correlations_path=correlation_dir / "cross_platform_correlations.json",
            output_dir=ranking_dir,
        ).build(
            clusters["globalPainClusters"],
            platform["platformPainProfiles"],
            market["marketIntelligenceMatrix"],
            correlation["crossPlatformCorrelations"],
        )
        report = SeasonalIntelligenceEngine(
            calendar_path=calendar_dir / "seasonal_calendar.json",
            trend_matches_path=trend_dir / "seasonal_trend_matches.json",
            trend_heatmap_path=trend_dir / "seasonal_market_heatmap.json",
            market_matrix_path=market_dir / "market_intelligence_matrix.json",
            ranked_intelligence_path=ranking_dir / "ranked_intelligence.json",
            output_dir=seasonal_intel_dir,
        ).build(
            calendar["seasonalCalendar"],
            trend["seasonalTrendMatches"],
            trend["seasonalMarketHeatmap"],
            market["marketIntelligenceMatrix"],
            ranking["rankedIntelligence"],
        )

        assert report["report_id"] == "SEASONAL_INTELLIGENCE_REPORT"
        assert report["round_id"] == "ROUND-GLOBAL-007"
        assert report["status"] == "seasonal_intelligence_ready"
        rows = report["seasonalIntelligence"]
        assert len({item["season_id"] for item in rows}) >= 6

        required_fields = {
            "season_id",
            "season_name",
            "market",
            "time_window",
            "likely_locations",
            "demand_keywords",
            "pain_clusters",
            "mobility_demand_types",
            "seasonal_heat_score",
            "confidence_score",
            "human_review_required",
        }
        for item in rows:
            assert required_fields.issubset(item)
            assert item["market"]
            assert item["time_window"]
            assert isinstance(item["seasonal_heat_score"], int)
            assert item["seasonal_heat_score"] >= 0
            assert item["human_review_required"] is True
            assert item["sample_data_only"] is True
            assert item["confirmed_prediction"] is False
            assert item["auto_publish_allowed"] is False
            assert item["auto_reply_allowed"] is False
            assert item["write_api_allowed"] is False

        summary = report["seasonalIntelligenceSummary"]
        assert summary["seasonal_intelligence_ready"] is True
        assert summary["season_count"] >= 6
        assert summary["sample_data_only"] is True
        assert summary["confirmed_prediction"] is False
        assert summary["real_external_api_connected"] is False
        assert summary["all_items_human_review_required"] is True
        assert summary["auto_publish_allowed"] is False
        assert summary["auto_reply_allowed"] is False
        assert summary["write_api_allowed"] is False

        assert report["seasonMarketHeatmap"]
        assert report["seasonalDemandRanking"]

        for output_name in [
            "SEASONAL_INTELLIGENCE_REPORT.json",
            "seasonal_intelligence.json",
            "season_market_heatmap.json",
            "seasonal_demand_ranking.json",
            "seasonal_intelligence_summary.json",
        ]:
            path = seasonal_intel_dir / output_name
            assert path.exists(), f"missing output: {output_name}"
            json.loads(path.read_text(encoding="utf-8"))

    print("seasonal_intelligence_engine_smoke_test passed")


if __name__ == "__main__":
    main()
