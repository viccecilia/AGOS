"""Demand prediction engine for global predictive intelligence."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from services.event_intelligence_engine import EventIntelligenceEngine
from services.external_drift_monitor import ExternalDriftMonitor
from services.intelligence_ranking_noise_filter import IntelligenceRankingNoiseFilter
from services.manual_external_feedback_intake import ManualExternalFeedbackIntake
from services.mobility_intelligence_engine import MobilityIntelligenceEngine
from services.runtime_persistence import utc_now_iso
from services.seasonal_intelligence_engine import SeasonalIntelligenceEngine
from services.spatial_intelligence_engine import SpatialIntelligenceEngine


DEFAULT_SEASONAL_INTELLIGENCE_PATH = Path("runtime/seasonal_intelligence/seasonal_intelligence.json")
DEFAULT_SPATIAL_INTELLIGENCE_PATH = Path("runtime/spatial_intelligence/spatial_intelligence.json")
DEFAULT_EVENT_INTELLIGENCE_PATH = Path("runtime/event_intelligence/event_intelligence.json")
DEFAULT_MOBILITY_INTELLIGENCE_PATH = Path("runtime/mobility_intelligence/mobility_intelligence.json")
DEFAULT_RANKED_INTELLIGENCE_PATH = Path("runtime/intelligence_ranking/ranked_intelligence.json")
DEFAULT_FEEDBACK_EVIDENCE_PATH = Path("runtime/manual_external_feedback_intake/manual_external_feedback_records.json")
DEFAULT_DRIFT_RESULT_PATH = Path("runtime/external_drift_monitor/external_drift_summary.json")
DEFAULT_OUTPUT_DIR = Path("runtime/demand_prediction")

PREDICTION_DIMENSIONS = [
    "time trend",
    "location trend",
    "event-driven spike",
    "platform signal trend",
    "market demand trend",
    "mobility demand trend",
]


class DemandPredictionEngine:
    """Generate reviewed demand predictions from predictive intelligence signals."""

    def __init__(
        self,
        seasonal_intelligence_path: str | Path = DEFAULT_SEASONAL_INTELLIGENCE_PATH,
        spatial_intelligence_path: str | Path = DEFAULT_SPATIAL_INTELLIGENCE_PATH,
        event_intelligence_path: str | Path = DEFAULT_EVENT_INTELLIGENCE_PATH,
        mobility_intelligence_path: str | Path = DEFAULT_MOBILITY_INTELLIGENCE_PATH,
        ranked_intelligence_path: str | Path = DEFAULT_RANKED_INTELLIGENCE_PATH,
        feedback_evidence_path: str | Path = DEFAULT_FEEDBACK_EVIDENCE_PATH,
        drift_result_path: str | Path = DEFAULT_DRIFT_RESULT_PATH,
        output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    ) -> None:
        self.seasonal_intelligence_path = Path(seasonal_intelligence_path)
        self.spatial_intelligence_path = Path(spatial_intelligence_path)
        self.event_intelligence_path = Path(event_intelligence_path)
        self.mobility_intelligence_path = Path(mobility_intelligence_path)
        self.ranked_intelligence_path = Path(ranked_intelligence_path)
        self.feedback_evidence_path = Path(feedback_evidence_path)
        self.drift_result_path = Path(drift_result_path)
        self.output_dir = Path(output_dir)
        self.report_path = self.output_dir / "DEMAND_PREDICTION_REPORT.json"
        self.predictions_path = self.output_dir / "demand_predictions.json"
        self.high_confidence_path = self.output_dir / "high_confidence_predictions.json"
        self.low_confidence_path = self.output_dir / "low_confidence_predictions.json"
        self.risk_review_path = self.output_dir / "prediction_risk_review.json"
        self.summary_path = self.output_dir / "demand_prediction_summary.json"

    def build(
        self,
        seasonal_intelligence: list[dict[str, Any]] | None = None,
        spatial_intelligence: list[dict[str, Any]] | None = None,
        event_intelligence: list[dict[str, Any]] | None = None,
        mobility_intelligence: list[dict[str, Any]] | None = None,
        ranked_intelligence: list[dict[str, Any]] | None = None,
        feedback_evidence: list[dict[str, Any]] | None = None,
        drift_result: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        seasonal = seasonal_intelligence if seasonal_intelligence is not None else self._load_seasonal_intelligence()
        spatial = spatial_intelligence if spatial_intelligence is not None else self._load_spatial_intelligence()
        events = event_intelligence if event_intelligence is not None else self._load_event_intelligence()
        mobility = mobility_intelligence if mobility_intelligence is not None else self._load_mobility_intelligence()
        ranked = ranked_intelligence if ranked_intelligence is not None else self._load_ranked_intelligence()
        feedback = feedback_evidence if feedback_evidence is not None else self._load_feedback_evidence()
        drift = drift_result if drift_result is not None else self._load_drift_result()

        predictions = self._predictions(seasonal, spatial, events, mobility, ranked, feedback, drift)
        high_confidence = [
            item
            for item in predictions
            if item["confidence_score"] >= 68 and item["predicted_heat_score"] >= 72 and not item["low_confidence"]
        ]
        low_confidence = [
            item
            for item in predictions
            if item["confidence_score"] < 68 or item["low_confidence"]
        ]
        risk_review = self._risk_review(predictions, high_confidence, low_confidence, drift)
        summary = self._summary(predictions, high_confidence, low_confidence, risk_review)
        report = {
            "report_id": "DEMAND_PREDICTION_REPORT",
            "round_id": "ROUND-GLOBAL-011",
            "created_at": utc_now_iso(),
            "status": "demand_prediction_ready",
            "phase": "GLOBAL_PREDICTIVE_INTELLIGENCE",
            "predictionDimensions": PREDICTION_DIMENSIONS,
            "demandPredictions": predictions,
            "highConfidencePredictions": high_confidence,
            "lowConfidencePredictions": low_confidence,
            "predictionRiskReview": risk_review,
            "demandPredictionSummary": summary,
            "safetyBoundary": "Demand Prediction Engine creates human-reviewed prediction candidates from local/sample/read-only intelligence. Sample data is not marked as real forecast truth, and no operational action, quote, dispatch, contact, publish, reply, DM, login, or write API call is allowed.",
        }
        self.persist(report)
        return report

    def state(self) -> dict[str, Any]:
        if self.report_path.exists():
            return json.loads(self.report_path.read_text(encoding="utf-8"))
        return self.build()

    def persist(self, report: dict[str, Any]) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.predictions_path.write_text(json.dumps(report["demandPredictions"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.high_confidence_path.write_text(json.dumps(report["highConfidencePredictions"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.low_confidence_path.write_text(json.dumps(report["lowConfidencePredictions"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.risk_review_path.write_text(json.dumps(report["predictionRiskReview"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.summary_path.write_text(json.dumps(report["demandPredictionSummary"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    def _load_seasonal_intelligence(self) -> list[dict[str, Any]]:
        if not self.seasonal_intelligence_path.exists():
            SeasonalIntelligenceEngine().build()
        return self._load_list(self.seasonal_intelligence_path)

    def _load_spatial_intelligence(self) -> list[dict[str, Any]]:
        if not self.spatial_intelligence_path.exists():
            SpatialIntelligenceEngine().build()
        return self._load_list(self.spatial_intelligence_path)

    def _load_event_intelligence(self) -> list[dict[str, Any]]:
        if not self.event_intelligence_path.exists():
            EventIntelligenceEngine().build()
        return self._load_list(self.event_intelligence_path)

    def _load_mobility_intelligence(self) -> list[dict[str, Any]]:
        if not self.mobility_intelligence_path.exists():
            MobilityIntelligenceEngine().build()
        return self._load_list(self.mobility_intelligence_path)

    def _load_ranked_intelligence(self) -> list[dict[str, Any]]:
        if not self.ranked_intelligence_path.exists():
            IntelligenceRankingNoiseFilter().build()
        return self._load_list(self.ranked_intelligence_path)

    def _load_feedback_evidence(self) -> list[dict[str, Any]]:
        if not self.feedback_evidence_path.exists():
            ManualExternalFeedbackIntake().build()
        return self._load_list(self.feedback_evidence_path)

    def _load_drift_result(self) -> dict[str, Any]:
        if not self.drift_result_path.exists():
            ExternalDriftMonitor().monitor()
        payload = json.loads(self.drift_result_path.read_text(encoding="utf-8")) if self.drift_result_path.exists() else {}
        return payload if isinstance(payload, dict) else {}

    @staticmethod
    def _load_list(path: Path) -> list[dict[str, Any]]:
        payload = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
        return payload if isinstance(payload, list) else []

    @classmethod
    def _predictions(
        cls,
        seasonal: list[dict[str, Any]],
        spatial: list[dict[str, Any]],
        events: list[dict[str, Any]],
        mobility: list[dict[str, Any]],
        ranked: list[dict[str, Any]],
        feedback: list[dict[str, Any]],
        drift: dict[str, Any],
    ) -> list[dict[str, Any]]:
        spatial_index = cls._spatial_index(spatial)
        event_index = cls._event_index(events)
        ranked_by_market = cls._ranked_by_market(ranked)
        feedback_strength = cls._feedback_strength(feedback)
        drift_penalty = cls._drift_penalty(drift)
        rows = []
        for index, item in enumerate(mobility[:36], start=1):
            location = item.get("location", "needs_review")
            market = cls._market(item.get("market", "needs_review"))
            season_name = item.get("season", "needs_review")
            spatial_match = spatial_index.get((market, location), spatial_index.get(("*", location), {}))
            event_match = event_index.get((market, item.get("event", "")), event_index.get(("*", item.get("event", "")), {}))
            seasonal_match = cls._seasonal_match(seasonal, market, season_name, location)
            ranked_match = ranked_by_market.get(market, ranked_by_market.get("*", []))[:3]
            heat = cls._predicted_heat(item, seasonal_match, spatial_match, event_match, ranked_match, feedback_strength, drift_penalty)
            confidence = cls._confidence(item, seasonal_match, spatial_match, event_match, ranked_match, feedback_strength, drift_penalty)
            low_confidence = confidence < 68 or item.get("noise_flag", False) or item.get("demand_type") == "no real mobility intent"
            rows.append(
                {
                    "prediction_id": f"DEMAND-PRED-{index:04d}",
                    "market": market,
                    "time_window": cls._time_window(item, seasonal_match, event_match),
                    "location": location,
                    "event": item.get("event", "none"),
                    "demand_type": item.get("demand_type", "needs_review"),
                    "prediction_dimension": cls._prediction_dimension(item, event_match, seasonal_match),
                    "predicted_heat_score": heat,
                    "confidence_score": confidence,
                    "evidence_sources": cls._evidence_sources(item, seasonal_match, spatial_match, event_match, ranked_match, feedback),
                    "risk_notes": cls._risk_notes(item, confidence, drift),
                    "sample_data_only": True,
                    "confirmed_real_prediction": False,
                    "low_confidence": low_confidence,
                    "human_review_required": True,
                    "action_allowed": False,
                    "auto_operational_action_allowed": False,
                    "auto_quote_allowed": False,
                    "auto_dispatch_allowed": False,
                    "auto_customer_contact_allowed": False,
                    "auto_driver_contact_allowed": False,
                    "auto_publish_allowed": False,
                    "auto_reply_allowed": False,
                    "write_api_allowed": False,
                }
            )
        rows.append(cls._low_confidence_noise_prediction(len(rows) + 1, drift))
        return sorted(rows, key=lambda row: (row["low_confidence"], -row["predicted_heat_score"], -row["confidence_score"]))

    @staticmethod
    def _spatial_index(spatial: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
        result: dict[tuple[str, str], dict[str, Any]] = {}
        for item in spatial:
            result[(item.get("market", "*"), item.get("location_name", ""))] = item
            result.setdefault(("*", item.get("location_name", "")), item)
        return result

    @staticmethod
    def _event_index(events: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
        result: dict[tuple[str, str], dict[str, Any]] = {}
        for item in events:
            result[(item.get("market", "*"), item.get("event_name", ""))] = item
            result.setdefault(("*", item.get("event_name", "")), item)
        return result

    @staticmethod
    def _ranked_by_market(ranked: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        result: dict[str, list[dict[str, Any]]] = {}
        for item in ranked:
            if item.get("ranking_status") not in {"high_value", "monitor"}:
                continue
            result.setdefault(item.get("market", "*"), []).append(item)
            result.setdefault("*", []).append(item)
        for key in result:
            result[key] = sorted(result[key], key=lambda row: row.get("total_score", 0), reverse=True)
        return result

    @staticmethod
    def _feedback_strength(feedback: list[dict[str, Any]]) -> int:
        accepted = [item for item in feedback if item.get("learning_memory_allowed")]
        if not accepted:
            return 0
        likes = sum(int(item.get("likes", 0)) for item in accepted)
        replies = sum(int(item.get("replies", 0)) for item in accepted)
        saves = sum(int(item.get("saves", 0)) for item in accepted)
        return min(12, round((likes * 0.2 + replies * 1.5 + saves * 0.8) / max(1, len(accepted))))

    @staticmethod
    def _drift_penalty(drift: dict[str, Any]) -> int:
        if drift.get("highest_severity") == "high":
            return 14
        if drift.get("highest_severity") == "medium":
            return 8
        return 0

    @staticmethod
    def _seasonal_match(seasonal: list[dict[str, Any]], market: str, season_name: str, location: str) -> dict[str, Any]:
        for item in seasonal:
            if item.get("market") == market and (item.get("season_name") == season_name or location in item.get("likely_locations", [])):
                return item
        for item in seasonal:
            if item.get("season_name") == season_name or location in item.get("likely_locations", []):
                return item
        return {}

    @staticmethod
    def _market(value: str) -> str:
        if "/" in value:
            return value.split("/")[0]
        return value or "needs_review"

    @staticmethod
    def _predicted_heat(
        item: dict[str, Any],
        seasonal: dict[str, Any],
        spatial: dict[str, Any],
        event: dict[str, Any],
        ranked: list[dict[str, Any]],
        feedback_strength: int,
        drift_penalty: int,
    ) -> int:
        mobility_heat = int(item.get("intent_strength", 0))
        seasonal_heat = int(seasonal.get("seasonal_heat_score", 0))
        spatial_heat = int(spatial.get("demand_heat_score", 0))
        event_heat = int(event.get("expected_crowd_pressure", 0))
        ranked_heat = round(sum(row.get("total_score", 0) for row in ranked) / max(1, len(ranked))) if ranked else 0
        heat = round(mobility_heat * 0.35 + seasonal_heat * 0.18 + spatial_heat * 0.2 + event_heat * 0.14 + ranked_heat * 0.1 + feedback_strength - drift_penalty)
        if item.get("noise_flag") or item.get("demand_type") == "no real mobility intent":
            heat = min(34, heat)
        return max(0, min(100, heat))

    @staticmethod
    def _confidence(
        item: dict[str, Any],
        seasonal: dict[str, Any],
        spatial: dict[str, Any],
        event: dict[str, Any],
        ranked: list[dict[str, Any]],
        feedback_strength: int,
        drift_penalty: int,
    ) -> int:
        mobility_confidence = 70 if item.get("source_type") in {"event_intelligence", "spatial_intelligence"} else 58
        seasonal_confidence = int(seasonal.get("confidence_score", 0))
        spatial_confidence = int(spatial.get("confidence_score", 0))
        event_confidence = int(event.get("confidence_score", 0))
        ranked_confidence = round(sum(row.get("score_breakdown", {}).get("evidence_confidence", 0) for row in ranked) / max(1, len(ranked))) if ranked else 0
        confidence = round(mobility_confidence * 0.28 + seasonal_confidence * 0.18 + spatial_confidence * 0.22 + event_confidence * 0.12 + ranked_confidence * 0.12 + feedback_strength - drift_penalty)
        if item.get("noise_flag") or item.get("demand_type") == "no real mobility intent":
            confidence = min(42, confidence)
        return max(0, min(100, confidence))

    @staticmethod
    def _time_window(item: dict[str, Any], seasonal: dict[str, Any], event: dict[str, Any]) -> str:
        if event.get("time_window"):
            return event["time_window"]
        if seasonal.get("time_window"):
            return seasonal["time_window"]
        if item.get("season"):
            return f"review_{item['season']}_window"
        return "needs_review"

    @staticmethod
    def _prediction_dimension(item: dict[str, Any], event: dict[str, Any], seasonal: dict[str, Any]) -> str:
        if item.get("source_type") == "mobility_demand_intent":
            return "mobility demand trend"
        if item.get("source_type") == "ranked_intelligence_noise_filter":
            return "platform signal trend"
        if event:
            return "event-driven spike"
        if item.get("source_type") == "spatial_intelligence":
            return "location trend"
        if seasonal:
            return "time trend"
        return "market demand trend"

    @staticmethod
    def _evidence_sources(
        item: dict[str, Any],
        seasonal: dict[str, Any],
        spatial: dict[str, Any],
        event: dict[str, Any],
        ranked: list[dict[str, Any]],
        feedback: list[dict[str, Any]],
    ) -> list[str]:
        sources = [f"mobility_intelligence:{item.get('mobility_id', '')}"]
        if seasonal:
            sources.append(f"seasonal_intelligence:{seasonal.get('season_id', '')}")
        if spatial:
            sources.append(f"spatial_intelligence:{spatial.get('location_id', '')}")
        if event:
            sources.append(f"event_intelligence:{event.get('event_id', '')}")
        sources.extend(f"ranked_intelligence:{row.get('intelligence_id', '')}" for row in ranked[:3])
        accepted_feedback = [row for row in feedback if row.get("learning_memory_allowed")]
        if accepted_feedback:
            sources.append(f"feedback_evidence:{accepted_feedback[0].get('feedback_intake_id', '')}")
        return [source for source in sources if not source.endswith(":")]

    @staticmethod
    def _risk_notes(item: dict[str, Any], confidence: int, drift: dict[str, Any]) -> str:
        notes = ["sample/read-only prediction candidate; requires human review"]
        if confidence < 68:
            notes.append("low confidence: do not route to action")
        if item.get("noise_flag") or item.get("demand_type") == "no real mobility intent":
            notes.append("noise or no real mobility intent")
        if drift.get("drift_signal_count", 0):
            notes.append(f"drift review present: {drift.get('highest_severity', 'unknown')}")
        return "; ".join(notes)

    @staticmethod
    def _low_confidence_noise_prediction(index: int, drift: dict[str, Any]) -> dict[str, Any]:
        return {
            "prediction_id": f"DEMAND-PRED-{index:04d}",
            "market": "Global English",
            "time_window": "none",
            "location": "unknown",
            "event": "none",
            "demand_type": "no real mobility intent",
            "prediction_dimension": "platform signal trend",
            "predicted_heat_score": 12,
            "confidence_score": 24,
            "evidence_sources": ["ranked_intelligence:noise_filtered_signals"],
            "risk_notes": "low-confidence/noise signal; do not route to action" + (f"; drift severity {drift.get('highest_severity')}" if drift else ""),
            "sample_data_only": True,
            "confirmed_real_prediction": False,
            "low_confidence": True,
            "human_review_required": True,
            "action_allowed": False,
            "auto_operational_action_allowed": False,
            "auto_quote_allowed": False,
            "auto_dispatch_allowed": False,
            "auto_customer_contact_allowed": False,
            "auto_driver_contact_allowed": False,
            "auto_publish_allowed": False,
            "auto_reply_allowed": False,
            "write_api_allowed": False,
        }

    @staticmethod
    def _risk_review(
        predictions: list[dict[str, Any]],
        high_confidence: list[dict[str, Any]],
        low_confidence: list[dict[str, Any]],
        drift: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "prediction_risk_review_ready": True,
            "prediction_count": len(predictions),
            "high_confidence_count": len(high_confidence),
            "low_confidence_count": len(low_confidence),
            "low_confidence_enters_action": False,
            "sample_data_marked_real_prediction": False,
            "all_predictions_human_review_required": all(item["human_review_required"] for item in predictions),
            "all_actions_blocked": all(item["action_allowed"] is False for item in predictions),
            "auto_operational_action_allowed": False,
            "auto_quote_allowed": False,
            "auto_dispatch_allowed": False,
            "auto_customer_contact_allowed": False,
            "auto_driver_contact_allowed": False,
            "auto_publish_allowed": False,
            "auto_reply_allowed": False,
            "write_api_allowed": False,
            "drift_signal_count": drift.get("drift_signal_count", 0),
            "drift_highest_severity": drift.get("highest_severity", "unknown"),
        }

    @staticmethod
    def _summary(
        predictions: list[dict[str, Any]],
        high_confidence: list[dict[str, Any]],
        low_confidence: list[dict[str, Any]],
        risk_review: dict[str, Any],
    ) -> dict[str, Any]:
        dimension_counts = Counter(item["prediction_dimension"] for item in predictions)
        return {
            "demand_prediction_ready": True,
            "prediction_count": len(predictions),
            "high_confidence_count": len(high_confidence),
            "low_confidence_count": len(low_confidence),
            "prediction_dimensions": dict(sorted(dimension_counts.items())),
            "markets": sorted({item["market"] for item in predictions}),
            "demand_types": sorted({item["demand_type"] for item in predictions}),
            "sample_data_only": True,
            "confirmed_real_predictions": False,
            "low_confidence_enters_action": risk_review["low_confidence_enters_action"],
            "all_predictions_human_review_required": risk_review["all_predictions_human_review_required"],
            "auto_operational_action_allowed": False,
            "auto_quote_allowed": False,
            "auto_dispatch_allowed": False,
            "auto_customer_contact_allowed": False,
            "auto_driver_contact_allowed": False,
            "auto_publish_allowed": False,
            "auto_reply_allowed": False,
            "write_api_allowed": False,
            "next_recommendation": "Use human-reviewed high-confidence predictions as input for Cross-Dimensional Correlation; never route low-confidence predictions to action.",
        }


if __name__ == "__main__":
    result = DemandPredictionEngine().build()
    print(json.dumps({"status": result["status"], "summary": result["demandPredictionSummary"]}, indent=2))
