"""Predictive Demand Gate for the Predictive Demand Intelligence phase."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.demand_to_action_strategy_engine import DemandToActionStrategyEngine
from services.location_demand_heatmap_engine import LocationDemandHeatmapEngine
from services.mobility_demand_intent_engine import MobilityDemandIntentEngine
from services.runtime_persistence import utc_now_iso
from services.seasonal_demand_calendar_engine import SeasonalDemandCalendarEngine


class PredictiveDemandGate:
    """Validate time, location, demand intent, action strategy, and safety boundary."""

    def __init__(self, root: str | Path = "runtime/predictive_demand_gate") -> None:
        self.root = Path(root)
        self.report_path = self.root / "PREDICTIVE_DEMAND_REPORT.json"
        self.safety_path = self.root / "DEMAND_INTELLIGENCE_SAFETY_REVIEW.json"
        self.checks_path = self.root / "predictive_demand_checks.json"
        self.summary_path = self.root / "predictive_demand_summary.json"

    def evaluate(self) -> dict[str, Any]:
        seasonal = SeasonalDemandCalendarEngine().state()
        heatmap = LocationDemandHeatmapEngine().state()
        intent = MobilityDemandIntentEngine().state()
        strategy = DemandToActionStrategyEngine().state()

        checks = self._checks(seasonal, heatmap, intent, strategy)
        safety_review = self._safety_review(seasonal, heatmap, intent, strategy)
        report = self._report(seasonal, heatmap, intent, strategy, checks, safety_review)
        summary = self._summary(checks, safety_review, report)
        payload = {
            "report_id": "PREDICTIVE_DEMAND_GATE",
            "created_at": utc_now_iso(),
            "status": "predictive_demand_gate_passed" if summary["gate_passed"] else "predictive_demand_gate_needs_review",
            "phase": "PREDICTIVE_DEMAND_INTELLIGENCE",
            "predictiveDemandReport": report,
            "demandIntelligenceSafetyReview": safety_review,
            "predictiveDemandChecks": checks,
            "predictiveDemandSummary": summary,
            "safetyBoundary": "Predictive Demand Gate validates local predictive intelligence only. It does not mark predictions as real outcomes, publish content, send DMs, quote prices, contact customers, contact drivers, contact businesses, dispatch vehicles, process payments, or call write APIs.",
        }
        self.persist(payload)
        return payload

    def state(self) -> dict[str, Any]:
        if self.report_path.exists():
            report = json.loads(self.report_path.read_text(encoding="utf-8"))
            safety = json.loads(self.safety_path.read_text(encoding="utf-8")) if self.safety_path.exists() else {}
            checks = json.loads(self.checks_path.read_text(encoding="utf-8")) if self.checks_path.exists() else []
            summary = json.loads(self.summary_path.read_text(encoding="utf-8")) if self.summary_path.exists() else {}
            return {
                "report_id": "PREDICTIVE_DEMAND_GATE",
                "status": "predictive_demand_gate_passed" if summary.get("gate_passed") else "predictive_demand_gate_needs_review",
                "predictiveDemandReport": report,
                "demandIntelligenceSafetyReview": safety,
                "predictiveDemandChecks": checks,
                "predictiveDemandSummary": summary,
            }
        return self.evaluate()

    def persist(self, payload: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text(json.dumps(payload["predictiveDemandReport"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.safety_path.write_text(json.dumps(payload["demandIntelligenceSafetyReview"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.checks_path.write_text(json.dumps(payload["predictiveDemandChecks"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.summary_path.write_text(json.dumps(payload["predictiveDemandSummary"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    @staticmethod
    def _checks(
        seasonal: dict[str, Any],
        heatmap: dict[str, Any],
        intent: dict[str, Any],
        strategy: dict[str, Any],
    ) -> list[dict[str, Any]]:
        seasonal_summary = seasonal.get("seasonalDemandSummary", {})
        heatmap_summary = heatmap.get("locationHeatmapSummary", {})
        intent_summary = intent.get("mobilityIntentSummary", {})
        strategy_summary = strategy.get("demandActionStrategySummary", {})
        return [
            {
                "check_id": "PREDICT-CHECK-001",
                "capability": "Seasonal Demand Calendar",
                "readiness_key": "time_trend_readiness",
                "status": "passed" if seasonal_summary.get("calendar_ready") and seasonal_summary.get("seasons", 0) >= 6 else "needs_review",
                "result": f"{seasonal_summary.get('seasons', 0)} seasons and {seasonal_summary.get('keywords', 0)} keywords available.",
                "evidence": ["seasonal_calendar.json", "seasonal_keywords.json", "seasonal_monitoring_plan.json"],
            },
            {
                "check_id": "PREDICT-CHECK-002",
                "capability": "Location Demand Heatmap",
                "readiness_key": "location_trend_readiness",
                "status": "passed" if heatmap_summary.get("heatmap_ready") and heatmap_summary.get("locations", 0) >= 10 else "needs_review",
                "result": f"{heatmap_summary.get('locations', 0)} locations and {heatmap_summary.get('hot_locations', 0)} hot locations available.",
                "evidence": ["location_heatmap.json", "location_mobility_risk.json", "location_heatmap_summary.json"],
            },
            {
                "check_id": "PREDICT-CHECK-003",
                "capability": "Mobility Demand Intent",
                "readiness_key": "demand_intent_readiness",
                "status": "passed" if intent_summary.get("intent_engine_ready") and intent_summary.get("high_value_intents", 0) > 0 and intent_summary.get("low_value_signals", 0) > 0 else "needs_review",
                "result": f"{intent_summary.get('high_value_intents', 0)} high-value intents and {intent_summary.get('low_value_signals', 0)} low-value signals separated.",
                "evidence": ["mobility_intents.json", "high_value_mobility_intents.json", "low_value_signals.json"],
            },
            {
                "check_id": "PREDICT-CHECK-004",
                "capability": "Demand-to-Action Strategy",
                "readiness_key": "action_strategy_readiness",
                "status": "passed" if strategy_summary.get("strategy_engine_ready") and strategy_summary.get("all_actions_need_human_review") else "needs_review",
                "result": f"{strategy_summary.get('total_actions', 0)} actions generated; human review required={strategy_summary.get('all_actions_need_human_review', False)}.",
                "evidence": ["platform_content_actions.json", "local_business_actions.json", "driver_operation_actions.json"],
            },
        ]

    @staticmethod
    def _safety_review(
        seasonal: dict[str, Any],
        heatmap: dict[str, Any],
        intent: dict[str, Any],
        strategy: dict[str, Any],
    ) -> dict[str, Any]:
        seasonal_summary = seasonal.get("seasonalDemandSummary", {})
        heatmap_summary = heatmap.get("locationHeatmapSummary", {})
        intent_summary = intent.get("mobilityIntentSummary", {})
        strategy_summary = strategy.get("demandActionStrategySummary", {})
        low_value_count = intent_summary.get("low_value_signals", 0)
        high_value_count = intent_summary.get("high_value_intents", 0)
        automated_flags = {
            "auto_publish_enabled": strategy_summary.get("auto_publish_enabled", False),
            "auto_dm_enabled": strategy_summary.get("auto_dm_enabled", False),
            "auto_quote_enabled": strategy_summary.get("auto_quote_enabled", False),
            "auto_contact_customer_enabled": strategy_summary.get("auto_contact_customer_enabled", False),
            "auto_contact_driver_enabled": strategy_summary.get("auto_contact_driver_enabled", False),
            "auto_contact_business_enabled": strategy_summary.get("auto_contact_business_enabled", False),
            "auto_dispatch_enabled": strategy_summary.get("auto_dispatch_enabled", False),
            "write_operations_enabled": strategy_summary.get("write_operations_enabled", False),
        }
        return {
            "review_id": "DEMAND_INTELLIGENCE_SAFETY_REVIEW",
            "created_at": utc_now_iso(),
            "sample_data_used": seasonal_summary.get("data_source") != "real_api_only" or heatmap_summary.get("data_source") != "real_time_crowd_data",
            "prediction_not_real_outcome": True,
            "real_time_crowd_data_connected": heatmap_summary.get("real_time_crowd_data_connected", False),
            "gps_dispatch_enabled": heatmap_summary.get("gps_dispatch_enabled", False),
            "low_value_filter_active": low_value_count > 0,
            "noise_marked_high_value_risk": "controlled" if low_value_count > 0 and high_value_count > 0 else "needs_review",
            "all_actions_human_gated": strategy_summary.get("all_actions_need_human_review", False),
            "automated_external_action_flags": automated_flags,
            "automatic_external_execution_enabled": any(automated_flags.values()),
            "requires_human_review": True,
            "risk_review": [
                {
                    "risk": "sample_data_interpreted_as_real_demand",
                    "status": "controlled",
                    "evidence": "Reports identify local sample/manual-import-ready data and prediction boundary.",
                    "mitigation": "Keep labels as predictive signals until live validated by human review.",
                },
                {
                    "risk": "noise_marked_as_high_value",
                    "status": "controlled" if low_value_count > 0 else "needs_review",
                    "evidence": f"{low_value_count} low-value signals separated from {high_value_count} high-value intents.",
                    "mitigation": "Continue human correction before operational use.",
                },
                {
                    "risk": "automatic_external_execution",
                    "status": "blocked" if not any(automated_flags.values()) else "needs_review",
                    "evidence": automated_flags,
                    "mitigation": "Do not enable posting, contacting, quoting, dispatch, or write APIs in this phase.",
                },
            ],
            "phase_exit_safety": "passed_with_human_gate" if not any(automated_flags.values()) else "blocked",
        }

    @staticmethod
    def _report(
        seasonal: dict[str, Any],
        heatmap: dict[str, Any],
        intent: dict[str, Any],
        strategy: dict[str, Any],
        checks: list[dict[str, Any]],
        safety_review: dict[str, Any],
    ) -> dict[str, Any]:
        seasonal_summary = seasonal.get("seasonalDemandSummary", {})
        heatmap_summary = heatmap.get("locationHeatmapSummary", {})
        intent_summary = intent.get("mobilityIntentSummary", {})
        strategy_summary = strategy.get("demandActionStrategySummary", {})
        readiness = {item["readiness_key"]: item["status"] == "passed" for item in checks}
        return {
            "report_id": "PREDICTIVE_DEMAND_REPORT",
            "created_at": utc_now_iso(),
            **readiness,
            "high_value_seasons": seasonal_summary.get("upcoming_peak_seasons", []),
            "high_value_locations": heatmap_summary.get("high_heat_locations", []),
            "high_value_mobility_intents": intent.get("highValueMobilityIntents", [])[:8],
            "recommended_actions": {
                "platform_content_actions": strategy.get("platformContentActions", [])[:8],
                "local_business_actions": strategy.get("localBusinessActions", [])[:8],
                "driver_operation_actions": strategy.get("driverOperationActions", [])[:8],
            },
            "risk_review": safety_review.get("risk_review", []),
            "next_phase_recommendation": "Controlled Real External Interaction Stage can start only as human-gated preparation. Keep all external actions blocked until explicit review.",
            "source_counts": {
                "seasons": seasonal_summary.get("seasons", 0),
                "locations": heatmap_summary.get("locations", 0),
                "high_value_intents": intent_summary.get("high_value_intents", 0),
                "recommended_actions": strategy_summary.get("total_actions", 0),
            },
        }

    @staticmethod
    def _summary(
        checks: list[dict[str, Any]],
        safety_review: dict[str, Any],
        report: dict[str, Any],
    ) -> dict[str, Any]:
        passed = len([item for item in checks if item["status"] == "passed"])
        blocked_external = safety_review.get("automatic_external_execution_enabled") is False
        gate_passed = passed == len(checks) and blocked_external and safety_review.get("all_actions_human_gated") is True
        return {
            "gate_ready": True,
            "checks": len(checks),
            "passed": passed,
            "gate_passed": gate_passed,
            "phase_completed": gate_passed,
            "time_trend_readiness": report.get("time_trend_readiness", False),
            "location_trend_readiness": report.get("location_trend_readiness", False),
            "demand_intent_readiness": report.get("demand_intent_readiness", False),
            "action_strategy_readiness": report.get("action_strategy_readiness", False),
            "next_phase": "CONTROLLED_REAL_EXTERNAL_INTERACTION_STAGE",
            "next_phase_recommendation": report.get("next_phase_recommendation", ""),
            "all_external_actions_human_gated": safety_review.get("all_actions_human_gated", False),
            "automatic_external_execution_enabled": safety_review.get("automatic_external_execution_enabled", True),
            "write_operations_enabled": safety_review.get("automated_external_action_flags", {}).get("write_operations_enabled", True),
        }


if __name__ == "__main__":
    result = PredictiveDemandGate().evaluate()
    print(json.dumps({"status": result["status"], "summary": result["predictiveDemandSummary"]}, indent=2))
