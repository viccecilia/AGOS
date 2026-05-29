from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.cross_dimensional_correlation import CrossDimensionalCorrelation
from services.cross_platform_correlation_expansion import CrossPlatformCorrelationExpansion
from services.demand_prediction_engine import DemandPredictionEngine
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
        platform_correlation_dir = root / "cross_platform_correlation"
        ranking_dir = root / "intelligence_ranking"
        seasonal_dir = root / "seasonal_intelligence"
        spatial_dir = root / "spatial_intelligence"
        event_dir = root / "event_intelligence"
        intent_dir = root / "mobility_demand_intent"
        mobility_dir = root / "mobility_intelligence"
        prediction_dir = root / "demand_prediction"
        cross_dimensional_dir = root / "cross_dimensional_correlation"

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
        platform_correlation = CrossPlatformCorrelationExpansion(
            platform_profiles_path=platform_dir / "platform_pain_profiles.json",
            market_matrix_path=market_dir / "market_intelligence_matrix.json",
            clusters_path=cluster_dir / "global_pain_clusters.json",
            output_dir=platform_correlation_dir,
        ).build(platform["platformPainProfiles"], market["marketIntelligenceMatrix"], clusters["globalPainClusters"])
        ranking = IntelligenceRankingNoiseFilter(
            clusters_path=cluster_dir / "global_pain_clusters.json",
            platform_profiles_path=platform_dir / "platform_pain_profiles.json",
            market_matrix_path=market_dir / "market_intelligence_matrix.json",
            correlations_path=platform_correlation_dir / "cross_platform_correlations.json",
            output_dir=ranking_dir,
        ).build(
            clusters["globalPainClusters"],
            platform["platformPainProfiles"],
            market["marketIntelligenceMatrix"],
            platform_correlation["crossPlatformCorrelations"],
        )
        seasonal = SeasonalIntelligenceEngine(
            calendar_path=calendar_dir / "seasonal_calendar.json",
            trend_matches_path=trend_dir / "seasonal_trend_matches.json",
            trend_heatmap_path=trend_dir / "seasonal_market_heatmap.json",
            market_matrix_path=market_dir / "market_intelligence_matrix.json",
            ranked_intelligence_path=ranking_dir / "ranked_intelligence.json",
            output_dir=seasonal_dir,
        ).build(
            calendar["seasonalCalendar"],
            trend["seasonalTrendMatches"],
            trend["seasonalMarketHeatmap"],
            market["marketIntelligenceMatrix"],
            ranking["rankedIntelligence"],
        )
        spatial = SpatialIntelligenceEngine(
            location_heatmap_path=location_dir / "location_heatmap.json",
            market_matrix_path=market_dir / "market_intelligence_matrix.json",
            seasonal_intelligence_path=seasonal_dir / "seasonal_intelligence.json",
            ranked_intelligence_path=ranking_dir / "ranked_intelligence.json",
            output_dir=spatial_dir,
        ).build(
            location["locationHeatmap"],
            market["marketIntelligenceMatrix"],
            seasonal["seasonalIntelligence"],
            ranking["rankedIntelligence"],
        )
        event = EventIntelligenceEngine(
            spatial_intelligence_path=spatial_dir / "spatial_intelligence.json",
            output_dir=event_dir,
        ).build(spatial["spatialIntelligence"])
        intents = MobilityDemandIntentEngine(intent_dir).build()
        mobility = MobilityIntelligenceEngine(
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
        feedback = [
            {
                "feedback_intake_id": "TEST-FEEDBACK-001",
                "platform": "Reddit",
                "likes": 18,
                "replies": 5,
                "saves": 7,
                "learning_memory_allowed": True,
            }
        ]
        drift = {
            "external_drift_monitor_ready": True,
            "drift_signal_count": 1,
            "highest_severity": "medium",
        }
        prediction = DemandPredictionEngine(
            seasonal_intelligence_path=seasonal_dir / "seasonal_intelligence.json",
            spatial_intelligence_path=spatial_dir / "spatial_intelligence.json",
            event_intelligence_path=event_dir / "event_intelligence.json",
            mobility_intelligence_path=mobility_dir / "mobility_intelligence.json",
            ranked_intelligence_path=ranking_dir / "ranked_intelligence.json",
            feedback_evidence_path=root / "feedback.json",
            drift_result_path=root / "drift.json",
            output_dir=prediction_dir,
        ).build(
            seasonal["seasonalIntelligence"],
            spatial["spatialIntelligence"],
            event["eventIntelligence"],
            mobility["mobilityIntelligence"],
            ranking["rankedIntelligence"],
            feedback,
            drift,
        )
        report = CrossDimensionalCorrelation(
            seasonal_intelligence_path=seasonal_dir / "seasonal_intelligence.json",
            spatial_intelligence_path=spatial_dir / "spatial_intelligence.json",
            event_intelligence_path=event_dir / "event_intelligence.json",
            mobility_intelligence_path=mobility_dir / "mobility_intelligence.json",
            demand_prediction_path=prediction_dir / "demand_predictions.json",
            platform_pain_path=platform_dir / "platform_pain_profiles.json",
            market_matrix_path=market_dir / "market_intelligence_matrix.json",
            output_dir=cross_dimensional_dir,
        ).build(
            seasonal["seasonalIntelligence"],
            spatial["spatialIntelligence"],
            event["eventIntelligence"],
            mobility["mobilityIntelligence"],
            prediction["demandPredictions"],
            platform["platformPainProfiles"],
            market["marketIntelligenceMatrix"],
        )

        assert report["report_id"] == "CROSS_DIMENSIONAL_CORRELATION_REPORT"
        assert report["round_id"] == "ROUND-GLOBAL-012"
        assert report["status"] == "cross_dimensional_correlation_ready"
        chains = report["correlationChains"]
        assert len(chains) >= 5
        required = {
            "correlation_id",
            "season",
            "location",
            "event",
            "market",
            "platform",
            "pain_cluster",
            "mobility_demand",
            "prediction",
            "why_correlated",
            "evidence_sources",
            "confidence_score",
            "recommended_strategy_type",
            "human_review_required",
        }
        for chain in chains:
            assert required.issubset(chain)
            assert chain["season"]
            assert chain["location"]
            assert chain["market"]
            assert chain["mobility_demand"]
            assert chain["why_correlated"]
            assert chain["evidence_sources"]
            assert chain["human_review_required"] is True
            assert chain["auto_publish_allowed"] is False
            assert chain["auto_contact_allowed"] is False
            assert chain["auto_dispatch_allowed"] is False
            assert chain["auto_quote_allowed"] is False
            assert chain["write_api_allowed"] is False
            assert chain["sample_data_only"] is True

        strategy = report["strategySignalCandidates"]
        assert strategy
        assert all(item["human_review_required"] is True for item in strategy)
        assert all(item["auto_publish_allowed"] is False for item in strategy)
        assert all(item["auto_contact_allowed"] is False for item in strategy)
        assert all(item["auto_dispatch_allowed"] is False for item in strategy)
        assert all(item["write_api_allowed"] is False for item in strategy)

        summary = report["crossDimensionalCorrelationSummary"]
        assert summary["cross_dimensional_correlation_ready"] is True
        assert summary["correlation_chain_count"] >= 5
        assert summary["all_chains_human_review_required"] is True
        assert summary["auto_publish_allowed"] is False
        assert summary["auto_contact_allowed"] is False
        assert summary["auto_dispatch_allowed"] is False
        assert summary["write_api_allowed"] is False

        for output_name in [
            "CROSS_DIMENSIONAL_CORRELATION_REPORT.json",
            "correlation_chains.json",
            "cross_dimension_heatmap.json",
            "strategy_signal_candidates.json",
            "cross_dimensional_correlation_summary.json",
        ]:
            path = cross_dimensional_dir / output_name
            assert path.exists(), f"missing output: {output_name}"
            json.loads(path.read_text(encoding="utf-8"))

    print("cross_dimensional_correlation_smoke_test passed")


if __name__ == "__main__":
    main()
