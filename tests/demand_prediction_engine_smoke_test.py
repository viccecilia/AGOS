from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

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
        correlation_dir = root / "cross_platform_correlation"
        ranking_dir = root / "intelligence_ranking"
        seasonal_dir = root / "seasonal_intelligence"
        spatial_dir = root / "spatial_intelligence"
        event_dir = root / "event_intelligence"
        intent_dir = root / "mobility_demand_intent"
        mobility_dir = root / "mobility_intelligence"
        prediction_dir = root / "demand_prediction"

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
        mobility = MobilityIntelligenceEngine(
            seasonal_intelligence_path=seasonal_dir / "seasonal_intelligence.json",
            spatial_intelligence_path=spatial_dir / "spatial_intelligence.json",
            event_intelligence_path=event_dir / "event_intelligence.json",
            mobility_intents_path=intent_dir / "mobility_intents.json",
            ranked_intelligence_path=ranking_dir / "ranked_intelligence.json",
            output_dir=mobility_dir,
        ).build(seasonal["seasonalIntelligence"], spatial["spatialIntelligence"], event["eventIntelligence"], intents["mobilityIntents"], ranking["rankedIntelligence"])

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
        report = DemandPredictionEngine(
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

        assert report["report_id"] == "DEMAND_PREDICTION_REPORT"
        assert report["round_id"] == "ROUND-GLOBAL-011"
        assert report["status"] == "demand_prediction_ready"
        predictions = report["demandPredictions"]
        assert len(predictions) >= 5

        required_fields = {
            "prediction_id",
            "market",
            "time_window",
            "location",
            "event",
            "demand_type",
            "predicted_heat_score",
            "confidence_score",
            "evidence_sources",
            "risk_notes",
            "sample_data_only",
            "human_review_required",
        }
        for item in predictions:
            assert required_fields.issubset(item)
            assert isinstance(item["confidence_score"], int)
            assert item["sample_data_only"] is True
            assert item["confirmed_real_prediction"] is False
            assert item["human_review_required"] is True
            assert item["auto_operational_action_allowed"] is False
            assert item["auto_quote_allowed"] is False
            assert item["auto_dispatch_allowed"] is False
            assert item["write_api_allowed"] is False

        high_confidence = report["highConfidencePredictions"]
        low_confidence = report["lowConfidencePredictions"]
        assert high_confidence
        assert low_confidence
        assert all(item["action_allowed"] is False for item in low_confidence)
        assert all(item["confidence_score"] < 68 or item["low_confidence"] for item in low_confidence)

        dimensions = {item["prediction_dimension"] for item in predictions}
        assert "event-driven spike" in dimensions
        assert "location trend" in dimensions or "time trend" in dimensions
        assert "mobility demand trend" in dimensions or "market demand trend" in dimensions

        risk = report["predictionRiskReview"]
        assert risk["low_confidence_enters_action"] is False
        assert risk["sample_data_marked_real_prediction"] is False
        assert risk["all_predictions_human_review_required"] is True
        assert risk["auto_operational_action_allowed"] is False
        assert risk["auto_dispatch_allowed"] is False
        assert risk["write_api_allowed"] is False

        summary = report["demandPredictionSummary"]
        assert summary["demand_prediction_ready"] is True
        assert summary["prediction_count"] >= 5
        assert summary["sample_data_only"] is True
        assert summary["confirmed_real_predictions"] is False
        assert summary["low_confidence_enters_action"] is False

        for output_name in [
            "DEMAND_PREDICTION_REPORT.json",
            "demand_predictions.json",
            "high_confidence_predictions.json",
            "low_confidence_predictions.json",
            "prediction_risk_review.json",
            "demand_prediction_summary.json",
        ]:
            path = prediction_dir / output_name
            assert path.exists(), f"missing output: {output_name}"
            json.loads(path.read_text(encoding="utf-8"))

    print("demand_prediction_engine_smoke_test passed")


if __name__ == "__main__":
    main()
