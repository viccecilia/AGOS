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
from services.mobility_demand_intent_engine import MobilityDemandIntentEngine
from services.mobility_intelligence_engine import MobilityIntelligenceEngine
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
        intent_dir = root / "mobility_demand_intent"
        mobility_dir = root / "mobility_intelligence"

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
        event = EventIntelligenceEngine(
            spatial_intelligence_path=spatial_dir / "spatial_intelligence.json",
            output_dir=event_dir,
        ).build(spatial["spatialIntelligence"])
        intents = MobilityDemandIntentEngine(intent_dir).build()
        report = MobilityIntelligenceEngine(
            seasonal_intelligence_path=seasonal_dir / "seasonal_intelligence.json",
            spatial_intelligence_path=spatial_dir / "spatial_intelligence.json",
            event_intelligence_path=event_dir / "event_intelligence.json",
            mobility_intents_path=intent_dir / "mobility_intents.json",
            ranked_intelligence_path=ranking_dir / "ranked_intelligence.json",
            output_dir=mobility_dir,
        ).build(
            seasonal["seasonalIntelligence"],
            spatial["spatialIntelligence"],
            event["eventIntelligence"],
            intents["mobilityIntents"],
            ranking["rankedIntelligence"],
        )

        assert report["report_id"] == "MOBILITY_INTELLIGENCE_REPORT"
        assert report["round_id"] == "ROUND-GLOBAL-010"
        assert report["status"] == "mobility_intelligence_ready"
        rows = report["mobilityIntelligence"]
        assert len(rows) >= 20

        required_fields = {
            "mobility_id",
            "market",
            "location",
            "season",
            "event",
            "demand_type",
            "intent_strength",
            "urgency_score",
            "conversion_potential",
            "recommended_route",
            "noise_flag",
            "human_review_required",
        }
        for item in rows:
            assert required_fields.issubset(item)
            assert item["human_review_required"] is True
            assert item["auto_quote_allowed"] is False
            assert item["auto_dispatch_allowed"] is False
            assert item["auto_customer_contact_allowed"] is False
            assert item["auto_driver_contact_allowed"] is False
            assert item["write_api_allowed"] is False

        demand_types = {item["demand_type"] for item in rows}
        assert "airport transfer" in demand_types
        assert "event pickup" in demand_types
        assert "no real mobility intent" in demand_types

        high_value = report["highValueMobilityDemand"]
        noise = report["mobilityNoiseSignals"]
        assert high_value
        assert noise
        assert all(item["noise_flag"] is False for item in high_value)
        assert all(item["demand_type"] != "no real mobility intent" for item in high_value)
        assert any(item["demand_type"] == "no real mobility intent" for item in noise)

        summary = report["mobilityIntelligenceSummary"]
        assert summary["mobility_intelligence_ready"] is True
        assert summary["airport_transfer_detected"] is True
        assert summary["event_pickup_detected"] is True
        assert summary["no_real_mobility_intent_detected"] is True
        assert summary["high_value_and_noise_separated"] is True
        assert summary["all_items_human_review_required"] is True
        assert summary["auto_quote_allowed"] is False
        assert summary["auto_dispatch_allowed"] is False
        assert summary["auto_customer_contact_allowed"] is False
        assert summary["auto_driver_contact_allowed"] is False
        assert summary["write_api_allowed"] is False

        for output_name in [
            "MOBILITY_INTELLIGENCE_REPORT.json",
            "mobility_intelligence.json",
            "high_value_mobility_demand.json",
            "mobility_noise_signals.json",
            "mobility_intelligence_summary.json",
        ]:
            path = mobility_dir / output_name
            assert path.exists(), f"missing output: {output_name}"
            json.loads(path.read_text(encoding="utf-8"))

    print("mobility_intelligence_engine_smoke_test passed")


if __name__ == "__main__":
    main()
