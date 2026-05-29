from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.cross_platform_correlation_expansion import CrossPlatformCorrelationExpansion
from services.event_intelligence_engine import EventIntelligenceEngine
from services.global_batch_intelligence_collection import GlobalBatchIntelligenceCollection
from services.global_pain_cluster_engine import GlobalPainClusterEngine
from services.intelligence_ranking_noise_filter import IntelligenceRankingNoiseFilter
from services.location_demand_heatmap_engine import LocationDemandHeatmapEngine
from services.market_intelligence_matrix import MarketIntelligenceMatrix
from services.platform_pain_intelligence import PlatformPainIntelligence
from services.seasonal_demand_calendar_engine import SeasonalDemandCalendarEngine
from services.seasonal_intelligence_engine import SeasonalIntelligenceEngine
from services.seasonal_trend_import_trial import SeasonalTrendImportTrial
from services.spatial_intelligence_engine import SpatialIntelligenceEngine


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        calendar_dir = root / "seasonal_demand_calendar"
        trend_dir = root / "seasonal_trend_import_trial"
        sample_dir = root / "import_samples"
        location_dir = root / "location_demand_heatmap"
        batch_dir = root / "global_batch_intelligence_collection"
        cluster_dir = root / "global_pain_clusters"
        platform_dir = root / "platform_pain_intelligence"
        market_dir = root / "market_intelligence_matrix"
        correlation_dir = root / "cross_platform_correlation"
        ranking_dir = root / "intelligence_ranking"
        seasonal_dir = root / "seasonal_intelligence"
        spatial_dir = root / "spatial_intelligence"
        event_dir = root / "event_intelligence"

        calendar = SeasonalDemandCalendarEngine(calendar_dir).build()
        sample_dir.mkdir(parents=True, exist_ok=True)
        sample_csv = PROJECT_ROOT / "runtime" / "seasonal_demand_calendar" / "import_samples" / "google_trends_japan_travel_sample.csv"
        (sample_dir / "google_trends_japan_travel_sample.csv").write_text(sample_csv.read_text(encoding="utf-8"), encoding="utf-8")
        trend = SeasonalTrendImportTrial(sample_dir=sample_dir, output_dir=trend_dir).run()
        location = LocationDemandHeatmapEngine(location_dir).build(calendar["seasonalCalendar"])
        batch = GlobalBatchIntelligenceCollection(batch_dir).collect()
        clusters = GlobalPainClusterEngine(input_path=batch_dir / "global_intelligence_records.json", output_dir=cluster_dir).build()
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
        ).build(batch["globalIntelligenceRecords"], clusters["globalPainClusters"], platform["platformPainProfiles"])
        correlation = CrossPlatformCorrelationExpansion(
            platform_profiles_path=platform_dir / "platform_pain_profiles.json",
            market_matrix_path=market_dir / "market_intelligence_matrix.json",
            clusters_path=cluster_dir / "global_pain_clusters.json",
            output_dir=correlation_dir,
        ).build(platform["platformPainProfiles"], market["marketIntelligenceMatrix"], clusters["globalPainClusters"])
        ranking = IntelligenceRankingNoiseFilter(
            clusters_path=cluster_dir / "global_pain_clusters.json",
            platform_profiles_path=platform_dir / "platform_pain_profiles.json",
            market_matrix_path=market_dir / "market_intelligence_matrix.json",
            correlations_path=correlation_dir / "cross_platform_correlations.json",
            output_dir=ranking_dir,
        ).build(clusters["globalPainClusters"], platform["platformPainProfiles"], market["marketIntelligenceMatrix"], correlation["crossPlatformCorrelations"])
        seasonal = SeasonalIntelligenceEngine(
            calendar_path=calendar_dir / "seasonal_calendar.json",
            trend_matches_path=trend_dir / "seasonal_trend_matches.json",
            trend_heatmap_path=trend_dir / "seasonal_market_heatmap.json",
            market_matrix_path=market_dir / "market_intelligence_matrix.json",
            ranked_intelligence_path=ranking_dir / "ranked_intelligence.json",
            output_dir=seasonal_dir,
        ).build(calendar["seasonalCalendar"], trend["seasonalTrendMatches"], trend["seasonalMarketHeatmap"], market["marketIntelligenceMatrix"], ranking["rankedIntelligence"])
        spatial = SpatialIntelligenceEngine(
            location_heatmap_path=location_dir / "location_heatmap.json",
            market_matrix_path=market_dir / "market_intelligence_matrix.json",
            seasonal_intelligence_path=seasonal_dir / "seasonal_intelligence.json",
            ranked_intelligence_path=ranking_dir / "ranked_intelligence.json",
            output_dir=spatial_dir,
        ).build(location["locationHeatmap"], market["marketIntelligenceMatrix"], seasonal["seasonalIntelligence"], ranking["rankedIntelligence"])
        report = EventIntelligenceEngine(
            spatial_intelligence_path=spatial_dir / "spatial_intelligence.json",
            output_dir=event_dir,
        ).build(spatial["spatialIntelligence"])

        assert report["report_id"] == "EVENT_INTELLIGENCE_REPORT"
        assert report["round_id"] == "ROUND-GLOBAL-009"
        assert report["status"] == "event_intelligence_ready"
        events = report["eventIntelligence"]
        assert len(events) >= 5

        required_fields = {
            "event_id",
            "event_name",
            "event_type",
            "market",
            "location",
            "time_window",
            "expected_crowd_pressure",
            "likely_mobility_demand",
            "related_keywords",
            "source_type",
            "confidence_score",
            "human_review_required",
        }
        for item in events:
            assert required_fields.issubset(item)
            assert item["location"]
            assert item["time_window"]
            assert item["likely_mobility_demand"]
            assert item["sample_event_only"] is True
            assert item["real_event_confirmed"] is False
            assert item["event_happened"] is False
            assert item["human_review_required"] is True
            assert item["auto_merchant_contact_allowed"] is False
            assert item["auto_driver_contact_allowed"] is False
            assert item["gps_dispatch_enabled"] is False
            assert item["write_api_allowed"] is False

        event_types = {item["event_type"] for item in events}
        assert {"concert", "sports event", "exhibition", "conference", "festival", "race", "product launch", "school holiday", "public holiday"} <= event_types

        summary = report["eventIntelligenceSummary"]
        assert summary["event_intelligence_ready"] is True
        assert summary["event_count"] >= 5
        assert summary["sample_event_only"] is True
        assert summary["real_events_confirmed"] is False
        assert summary["event_happened_marked_true"] is False
        assert summary["all_items_human_review_required"] is True
        assert summary["auto_merchant_contact_allowed"] is False
        assert summary["auto_driver_contact_allowed"] is False
        assert summary["gps_dispatch_enabled"] is False
        assert summary["write_api_allowed"] is False

        assert report["eventLocationHeatmap"]
        assert report["eventMobilityDemand"]

        for output_name in [
            "EVENT_INTELLIGENCE_REPORT.json",
            "event_intelligence.json",
            "event_location_heatmap.json",
            "event_mobility_demand.json",
            "event_intelligence_summary.json",
        ]:
            path = event_dir / output_name
            assert path.exists(), f"missing output: {output_name}"
            json.loads(path.read_text(encoding="utf-8"))

    print("event_intelligence_engine_smoke_test passed")


if __name__ == "__main__":
    main()
