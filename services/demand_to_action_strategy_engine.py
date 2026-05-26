"""Demand-to-action strategy engine for predictive demand intelligence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.api_collection_review_and_correction import APICollectionReviewAndCorrection
from services.live_data_import_to_memory import LiveDataImportToMemory
from services.location_demand_heatmap_engine import LocationDemandHeatmapEngine
from services.mobility_demand_intent_engine import MobilityDemandIntentEngine
from services.runtime_persistence import utc_now_iso
from services.seasonal_demand_calendar_engine import SeasonalDemandCalendarEngine


CONTENT_PLATFORM_TEMPLATES = [
    {
        "target_platform": "Reddit",
        "content_type": "Reddit post idea",
        "recommended_tone": "trusted_guide",
        "angle_template": "Explain the safest choice for {pain_point} around {location} without hard selling.",
    },
    {
        "target_platform": "TikTok",
        "content_type": "TikTok short video hook",
        "recommended_tone": "fast_emotional_hook",
        "angle_template": "Hook: If {location} feels confusing during {season}, avoid this transfer mistake.",
    },
    {
        "target_platform": "X",
        "content_type": "X trend post",
        "recommended_tone": "concise_signal",
        "angle_template": "Short trend note: {location} demand is rising for {pain_point}; plan before peak windows.",
    },
    {
        "target_platform": "YouTube",
        "content_type": "YouTube topic",
        "recommended_tone": "clear_planner",
        "angle_template": "Topic: How to handle {pain_point} in {location} during {season}.",
    },
    {
        "target_platform": "Instagram",
        "content_type": "Instagram carousel idea",
        "recommended_tone": "visual_calm",
        "angle_template": "Carousel: {location} arrival checklist for travelers with {pain_point}.",
    },
    {
        "target_platform": "Xiaohongshu",
        "content_type": "小红书内容选题",
        "recommended_tone": "practical_local_tip",
        "angle_template": "{location} {season} 出行避坑：{pain_point} 怎么提前准备。",
    },
    {
        "target_platform": "SEO / Website",
        "content_type": "SEO article topic",
        "recommended_tone": "search_helpful",
        "angle_template": "SEO guide: {location} transfer options for {pain_point} during {season}.",
    },
]

BUSINESS_TYPES = [
    "charter_company",
    "airport_transfer_company",
    "travel_agency",
    "hotel",
    "local_dmc",
    "exhibition_service_provider",
    "event_organizer",
]

BUSINESS_LABELS = {
    "airport_transfer": ["airport_transfer_company", "hotel", "travel_agency"],
    "private_charter": ["charter_company", "travel_agency", "local_dmc"],
    "family_trip": ["charter_company", "hotel", "travel_agency"],
    "elderly_support": ["charter_company", "local_dmc", "hotel"],
    "luggage_heavy_trip": ["airport_transfer_company", "hotel", "local_dmc"],
    "night_arrival": ["airport_transfer_company", "hotel"],
    "multi_city_transfer": ["charter_company", "travel_agency", "local_dmc"],
    "event_pickup": ["exhibition_service_provider", "event_organizer", "charter_company"],
    "station_to_hotel": ["hotel", "airport_transfer_company", "local_dmc"],
    "sightseeing_route": ["charter_company", "travel_agency", "local_dmc"],
    "price_comparison": ["travel_agency"],
    "public_transport_anxiety": ["travel_agency", "hotel", "local_dmc"],
}


class DemandToActionStrategyEngine:
    """Convert time, location, and mobility intent signals into human-gated actions."""

    def __init__(self, root: str | Path = "runtime/demand_to_action_strategy") -> None:
        self.root = Path(root)
        self.report_path = self.root / "demand_action_strategy_report.json"
        self.platform_path = self.root / "platform_content_actions.json"
        self.business_path = self.root / "local_business_actions.json"
        self.driver_path = self.root / "driver_operation_actions.json"
        self.summary_path = self.root / "demand_action_strategy_summary.json"

    def build(self) -> dict[str, Any]:
        seasonal = SeasonalDemandCalendarEngine().state()
        location_heatmap = LocationDemandHeatmapEngine().state()
        mobility_intent = MobilityDemandIntentEngine().state()
        live_memory_import = LiveDataImportToMemory().state()
        collection_review = APICollectionReviewAndCorrection().state()
        high_value_intents = mobility_intent.get("highValueMobilityIntents", [])
        platform_actions = self._platform_actions(high_value_intents, seasonal, location_heatmap)
        business_actions = self._business_actions(high_value_intents, seasonal, location_heatmap)
        driver_actions = self._driver_actions(high_value_intents, location_heatmap)
        summary = self._summary(
            platform_actions,
            business_actions,
            driver_actions,
            seasonal,
            location_heatmap,
            mobility_intent,
            live_memory_import,
            collection_review,
        )
        report = {
            "report_id": "DEMAND_ACTION_STRATEGY_REPORT",
            "created_at": utc_now_iso(),
            "status": "demand_action_strategy_ready",
            "phase": "PREDICTIVE_DEMAND_INTELLIGENCE",
            "inputs": {
                "seasonal_demand_calendar": seasonal.get("status", "unknown"),
                "location_demand_heatmap": location_heatmap.get("status", "unknown"),
                "mobility_demand_intent": mobility_intent.get("status", "unknown"),
                "live_memory_import": live_memory_import.get("status", "unknown"),
                "collection_review_correction": collection_review.get("status", "unknown"),
            },
            "platformContentActions": platform_actions,
            "localBusinessActions": business_actions,
            "driverOperationActions": driver_actions,
            "demandActionStrategySummary": summary,
            "safetyBoundary": "Demand-to-Action Strategy Engine generates human-reviewed local recommendations only. It does not post, DM, quote, contact customers, contact drivers, dispatch vehicles, contact businesses, process payment, or call write APIs.",
        }
        self.persist(report)
        return report

    def state(self) -> dict[str, Any]:
        if self.report_path.exists():
            return json.loads(self.report_path.read_text(encoding="utf-8"))
        return self.build()

    def persist(self, report: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.platform_path.write_text(json.dumps(report["platformContentActions"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.business_path.write_text(json.dumps(report["localBusinessActions"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.driver_path.write_text(json.dumps(report["driverOperationActions"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.summary_path.write_text(json.dumps(report["demandActionStrategySummary"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    @staticmethod
    def _platform_actions(
        intents: list[dict[str, Any]],
        seasonal: dict[str, Any],
        heatmap: dict[str, Any],
    ) -> list[dict[str, Any]]:
        actions: list[dict[str, Any]] = []
        top_intents = DemandToActionStrategyEngine._top_intents(intents, 3)
        for intent in top_intents:
            pain_point = intent.get("demand_intent", "mobility_demand")
            location = intent.get("location") or "Japan"
            season = intent.get("season") or DemandToActionStrategyEngine._current_season(seasonal)
            audience = DemandToActionStrategyEngine._audience(intent)
            risk_level = DemandToActionStrategyEngine._risk_level(intent)
            for index, template in enumerate(CONTENT_PLATFORM_TEMPLATES, start=1):
                action_id = f"PLATFORM-ACTION-{len(actions) + 1:04d}"
                actions.append(
                    {
                        "action_id": action_id,
                        "source_intent_id": intent.get("intent_id", ""),
                        "target_platform": template["target_platform"],
                        "content_type": template["content_type"],
                        "content_angle": template["angle_template"].format(
                            pain_point=pain_point.replace("_", " "),
                            location=location,
                            season=season,
                        ),
                        "pain_point": pain_point,
                        "season": season,
                        "location": location,
                        "audience": audience,
                        "recommended_tone": template["recommended_tone"],
                        "risk_level": risk_level,
                        "reason": DemandToActionStrategyEngine._reason(intent, heatmap),
                        "human_review_required": True,
                        "status": "needs_human_review",
                        "auto_publish_enabled": False,
                        "auto_reply_enabled": False,
                        "auto_dm_enabled": False,
                        "created_at": utc_now_iso(),
                    }
                )
        return actions

    @staticmethod
    def _business_actions(
        intents: list[dict[str, Any]],
        seasonal: dict[str, Any],
        heatmap: dict[str, Any],
    ) -> list[dict[str, Any]]:
        actions: list[dict[str, Any]] = []
        top_intents = DemandToActionStrategyEngine._top_intents(intents, 5)
        for intent in top_intents:
            demand = intent.get("demand_intent", "")
            for business_type in BUSINESS_LABELS.get(demand, ["travel_agency"])[:3]:
                location = intent.get("location") or "Japan"
                season = intent.get("season") or DemandToActionStrategyEngine._current_season(seasonal)
                actions.append(
                    {
                        "action_id": f"BUSINESS-ACTION-{len(actions) + 1:04d}",
                        "source_intent_id": intent.get("intent_id", ""),
                        "business_type": business_type,
                        "opportunity": f"{demand} demand is emerging around {location}.",
                        "target_location": location,
                        "target_time_window": season,
                        "recommended_offer": DemandToActionStrategyEngine._recommended_offer(demand, business_type),
                        "required_preparation": DemandToActionStrategyEngine._business_preparation(demand, location, heatmap),
                        "risk_notes": DemandToActionStrategyEngine._business_risk_notes(intent),
                        "reason": DemandToActionStrategyEngine._reason(intent, heatmap),
                        "human_review_required": True,
                        "status": "needs_human_review",
                        "auto_contact_business_enabled": False,
                        "auto_contact_customer_enabled": False,
                        "auto_quote_enabled": False,
                        "created_at": utc_now_iso(),
                    }
                )
        existing = {item["business_type"] for item in actions}
        fallback_intent = top_intents[0] if top_intents else {}
        for business_type in BUSINESS_TYPES:
            if business_type in existing:
                continue
            location = fallback_intent.get("location") or "Japan"
            season = fallback_intent.get("season") or DemandToActionStrategyEngine._current_season(seasonal)
            demand = fallback_intent.get("demand_intent", "mobility_demand")
            actions.append(
                {
                    "action_id": f"BUSINESS-ACTION-{len(actions) + 1:04d}",
                    "source_intent_id": fallback_intent.get("intent_id", ""),
                    "business_type": business_type,
                    "opportunity": f"{business_type} should monitor {demand} demand around {location}.",
                    "target_location": location,
                    "target_time_window": season,
                    "recommended_offer": DemandToActionStrategyEngine._recommended_offer(demand, business_type),
                    "required_preparation": DemandToActionStrategyEngine._business_preparation(demand, location, heatmap),
                    "risk_notes": "Preparation-only suggestion. Do not contact businesses, customers, drivers, or venues automatically.",
                    "reason": DemandToActionStrategyEngine._reason(fallback_intent, heatmap),
                    "human_review_required": True,
                    "status": "needs_human_review",
                    "auto_contact_business_enabled": False,
                    "auto_contact_customer_enabled": False,
                    "auto_quote_enabled": False,
                    "created_at": utc_now_iso(),
                }
            )
        return actions

    @staticmethod
    def _driver_actions(
        intents: list[dict[str, Any]],
        heatmap: dict[str, Any],
    ) -> list[dict[str, Any]]:
        actions: list[dict[str, Any]] = []
        for intent in DemandToActionStrategyEngine._top_intents(intents, 6):
            location = intent.get("location") or "Japan"
            demand = intent.get("demand_intent", "")
            location_record = DemandToActionStrategyEngine._location_record(location, heatmap)
            actions.append(
                {
                    "action_id": f"DRIVER-ACTION-{len(actions) + 1:04d}",
                    "source_intent_id": intent.get("intent_id", ""),
                    "focus_standby_area": location,
                    "priority_time_window": DemandToActionStrategyEngine._driver_time_window(intent),
                    "recommended_vehicle_type": DemandToActionStrategyEngine._vehicle_type(demand),
                    "language_preparation": DemandToActionStrategyEngine._language_preparation(intent),
                    "luggage_space_requirement": DemandToActionStrategyEngine._luggage_requirement(demand, location_record),
                    "traffic_waiting_risk": DemandToActionStrategyEngine._traffic_waiting_risk(intent, location_record),
                    "service_script_suggestion": DemandToActionStrategyEngine._service_script(demand, location),
                    "reason": DemandToActionStrategyEngine._reason(intent, heatmap),
                    "human_review_required": True,
                    "status": "needs_human_review",
                    "auto_dispatch_enabled": False,
                    "auto_contact_driver_enabled": False,
                    "auto_contact_customer_enabled": False,
                    "auto_quote_enabled": False,
                    "created_at": utc_now_iso(),
                }
            )
        return actions

    @staticmethod
    def _top_intents(intents: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
        return sorted(
            intents,
            key=lambda item: (
                item.get("conversion_potential_score", 0),
                item.get("urgency_score", 0),
                item.get("intent_strength_score", 0),
            ),
            reverse=True,
        )[:limit]

    @staticmethod
    def _current_season(seasonal: dict[str, Any]) -> str:
        return seasonal.get("seasonalDemandSummary", {}).get("current_focus_season", "seasonal demand window")

    @staticmethod
    def _audience(intent: dict[str, Any]) -> str:
        demand = intent.get("demand_intent", "")
        if demand in {"family_trip", "elderly_support", "luggage_heavy_trip"}:
            return "families and travelers carrying luggage"
        if demand == "event_pickup":
            return "event visitors and group travelers"
        if demand == "airport_transfer":
            return "inbound travelers arriving in Japan"
        return "Japan trip planners"

    @staticmethod
    def _risk_level(intent: dict[str, Any]) -> str:
        score = max(intent.get("urgency_score", 0), intent.get("conversion_potential_score", 0))
        return "high" if score >= 82 else "medium" if score >= 62 else "low"

    @staticmethod
    def _reason(intent: dict[str, Any], heatmap: dict[str, Any]) -> str:
        location = intent.get("location") or "unknown"
        location_record = DemandToActionStrategyEngine._location_record(location, heatmap)
        heat = location_record.get("demand_heat_score", "unknown")
        return (
            f"{intent.get('demand_intent')} signal has strength {intent.get('intent_strength_score')} "
            f"and conversion {intent.get('conversion_potential_score')} around {location}; "
            f"location heat score is {heat}. Action remains human-reviewed only."
        )

    @staticmethod
    def _location_record(location: str, heatmap: dict[str, Any]) -> dict[str, Any]:
        for item in heatmap.get("locationHeatmap", []):
            if item.get("location_name") == location:
                return item
        return {}

    @staticmethod
    def _recommended_offer(demand: str, business_type: str) -> str:
        if demand == "airport_transfer":
            return "Human-reviewed airport arrival transfer package with luggage and late-arrival guidance."
        if demand == "event_pickup":
            return "Event exit pickup plan with pre-agreed meeting points and waiting-time disclosure."
        if demand in {"private_charter", "sightseeing_route"}:
            return "Private route planning offer with flexible sightseeing stops."
        if demand in {"family_trip", "elderly_support", "luggage_heavy_trip"}:
            return "Comfort-focused transfer offer for families, seniors, and luggage-heavy trips."
        return f"Prepare a human-reviewed {business_type} offer for {demand}."

    @staticmethod
    def _business_preparation(demand: str, location: str, heatmap: dict[str, Any]) -> list[str]:
        record = DemandToActionStrategyEngine._location_record(location, heatmap)
        prep = ["human review before any outreach", "verify real inventory before promising service"]
        if demand in {"airport_transfer", "night_arrival"}:
            prep += ["airport arrival timing checklist", "late-arrival support script"]
        if demand in {"family_trip", "elderly_support", "luggage_heavy_trip"}:
            prep += ["larger luggage capacity", "walking-distance reduction plan"]
        if demand == "event_pickup":
            prep += ["venue pickup map", "post-event waiting-time policy"]
        if record.get("driver_vehicle_preparation_required"):
            prep.append("pre-check driver and vehicle availability")
        return prep

    @staticmethod
    def _business_risk_notes(intent: dict[str, Any]) -> str:
        return (
            f"Do not contact customers or businesses automatically. Validate {intent.get('location')} demand, "
            "inventory, timing, and legal/commercial constraints manually."
        )

    @staticmethod
    def _driver_time_window(intent: dict[str, Any]) -> str:
        demand = intent.get("demand_intent", "")
        if demand in {"night_arrival", "airport_transfer"}:
            return "arrival_peak_and_late_evening"
        if demand == "event_pickup":
            return "event_exit_window"
        return intent.get("season") or "seasonal_peak_window"

    @staticmethod
    def _vehicle_type(demand: str) -> str:
        if demand in {"family_trip", "luggage_heavy_trip", "airport_transfer"}:
            return "minivan_or_large_luggage_vehicle"
        if demand == "event_pickup":
            return "van_or_group_transfer_vehicle"
        if demand in {"private_charter", "sightseeing_route", "elderly_support"}:
            return "comfortable_private_charter_vehicle"
        return "standard_transfer_vehicle"

    @staticmethod
    def _language_preparation(intent: dict[str, Any]) -> list[str]:
        market = intent.get("market", "")
        languages = ["simple English pickup script", "Japanese driver notes"]
        if "Taiwan" in market or "China" in market:
            languages.append("Chinese pickup instructions")
        if "Korea" in market:
            languages.append("Korean pickup instructions")
        return languages

    @staticmethod
    def _luggage_requirement(demand: str, location_record: dict[str, Any]) -> str:
        if demand in {"airport_transfer", "luggage_heavy_trip", "family_trip"}:
            return "large_luggage_capacity_required"
        if location_record.get("luggage_difficulty_score", 0) >= 82:
            return "medium_to_large_luggage_capacity_recommended"
        return "standard_luggage_capacity"

    @staticmethod
    def _traffic_waiting_risk(intent: dict[str, Any], location_record: dict[str, Any]) -> str:
        if intent.get("demand_intent") == "event_pickup":
            return "high_event_exit_waiting_risk"
        heat = location_record.get("demand_heat_score", 0)
        return "high_congestion_waiting_risk" if heat >= 85 else "medium_waiting_risk"

    @staticmethod
    def _service_script(demand: str, location: str) -> str:
        if demand == "airport_transfer":
            return f"Confirm terminal, luggage count, arrival time, and exact meeting point for {location}."
        if demand == "event_pickup":
            return f"Confirm post-event pickup gate, walking route, waiting policy, and backup point for {location}."
        if demand in {"family_trip", "elderly_support"}:
            return f"Confirm walking limits, luggage count, child/senior support, and rest stops around {location}."
        return f"Confirm route, luggage, timing, and human-reviewed service boundary around {location}."

    @staticmethod
    def _summary(
        platform_actions: list[dict[str, Any]],
        business_actions: list[dict[str, Any]],
        driver_actions: list[dict[str, Any]],
        seasonal: dict[str, Any],
        heatmap: dict[str, Any],
        mobility_intent: dict[str, Any],
        live_memory_import: dict[str, Any],
        collection_review: dict[str, Any],
    ) -> dict[str, Any]:
        all_actions = platform_actions + business_actions + driver_actions
        return {
            "strategy_engine_ready": True,
            "platform_content_actions": len(platform_actions),
            "local_business_actions": len(business_actions),
            "driver_operation_actions": len(driver_actions),
            "total_actions": len(all_actions),
            "all_actions_need_human_review": all(item.get("status") == "needs_human_review" for item in all_actions),
            "source_seasons": seasonal.get("seasonalDemandSummary", {}).get("seasons", 0),
            "source_locations": heatmap.get("locationHeatmapSummary", {}).get("locations", 0),
            "source_high_value_intents": mobility_intent.get("mobilityIntentSummary", {}).get("high_value_intents", 0),
            "source_memory_imports": live_memory_import.get("memoryImportSummary", {}).get("normalized_items", 0),
            "source_collection_review_items": collection_review.get("collectionReviewSummary", {}).get("review_queue_items", 0),
            "target_platforms": sorted({item.get("target_platform", "") for item in platform_actions}),
            "business_types": sorted({item.get("business_type", "") for item in business_actions}),
            "driver_focus_areas": sorted({item.get("focus_standby_area", "") for item in driver_actions}),
            "auto_publish_enabled": False,
            "auto_dm_enabled": False,
            "auto_quote_enabled": False,
            "auto_contact_customer_enabled": False,
            "auto_contact_driver_enabled": False,
            "auto_contact_business_enabled": False,
            "auto_dispatch_enabled": False,
            "write_operations_enabled": False,
        }


if __name__ == "__main__":
    result = DemandToActionStrategyEngine().build()
    print(json.dumps({"status": result["status"], "summary": result["demandActionStrategySummary"]}, indent=2))
