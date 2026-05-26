"""Location demand heatmap for Japan mobility demand prediction."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.runtime_persistence import utc_now_iso
from services.seasonal_demand_calendar_engine import SeasonalDemandCalendarEngine


LOCATION_DATA_SOURCE = "local_sample_and_seasonal_calendar_ready"


DEFAULT_LOCATIONS: list[dict[str, Any]] = [
    {
        "location_id": "LOC-TOKYO",
        "location_name": "Tokyo",
        "location_type": "city",
        "region": "Kanto",
        "base_related_seasons": ["Sakura Season", "Golden Week", "Christmas and Year End", "Chinese New Year Travel"],
        "related_events": ["citywide seasonal travel", "airport arrival peaks", "shopping and hotel district movement"],
        "mobility_demand_types": ["airport_transfer", "station_to_hotel", "private_charter", "night_arrival"],
        "common_pain_points": ["complex rail transfers", "large luggage", "hotel district congestion", "first Japan trip anxiety"],
        "crowd_risk_score": 88,
        "transfer_complexity_score": 92,
        "luggage_difficulty_score": 86,
    },
    {
        "location_id": "LOC-HANEDA",
        "location_name": "Haneda Airport",
        "location_type": "airport",
        "region": "Tokyo",
        "base_related_seasons": ["Chinese New Year Travel", "Golden Week", "Japan New Year"],
        "related_events": ["international arrivals", "late-night arrivals"],
        "mobility_demand_types": ["airport_transfer", "family_group_transfer", "night_arrival", "luggage_heavy_trip"],
        "common_pain_points": ["late train anxiety", "airport queue uncertainty", "large luggage", "language support"],
        "crowd_risk_score": 82,
        "transfer_complexity_score": 80,
        "luggage_difficulty_score": 90,
    },
    {
        "location_id": "LOC-NARITA",
        "location_name": "Narita Airport",
        "location_type": "airport",
        "region": "Chiba",
        "base_related_seasons": ["Chinese New Year Travel", "Sakura Season", "Golden Week"],
        "related_events": ["long-distance airport transfers", "inbound peak arrivals"],
        "mobility_demand_types": ["airport_transfer", "multi_city_transfer", "family_group_transfer", "luggage_heavy_trip"],
        "common_pain_points": ["long transfer distance", "rail transfer confusion", "large luggage", "arrival fatigue"],
        "crowd_risk_score": 80,
        "transfer_complexity_score": 88,
        "luggage_difficulty_score": 91,
    },
    {
        "location_id": "LOC-SHINJUKU",
        "location_name": "Shinjuku",
        "location_type": "commercial_district",
        "region": "Tokyo",
        "base_related_seasons": ["Sakura Season", "Christmas and Year End", "Golden Week"],
        "related_events": ["hotel district arrivals", "night entertainment movement"],
        "mobility_demand_types": ["station_to_hotel", "night_arrival", "local_transfer"],
        "common_pain_points": ["station maze", "hotel pickup confusion", "night crowding", "large luggage"],
        "crowd_risk_score": 86,
        "transfer_complexity_score": 94,
        "luggage_difficulty_score": 82,
    },
    {
        "location_id": "LOC-SHIBUYA",
        "location_name": "Shibuya",
        "location_type": "commercial_district",
        "region": "Tokyo",
        "base_related_seasons": ["Christmas and Year End", "Golden Week"],
        "related_events": ["shopping peaks", "night events", "youth travel trends"],
        "mobility_demand_types": ["hotel_transfer", "night_arrival", "local_transfer"],
        "common_pain_points": ["crowded crossings", "pickup point confusion", "late return", "shopping luggage"],
        "crowd_risk_score": 85,
        "transfer_complexity_score": 82,
        "luggage_difficulty_score": 76,
    },
    {
        "location_id": "LOC-UENO",
        "location_name": "Ueno",
        "location_type": "attraction",
        "region": "Tokyo",
        "base_related_seasons": ["Sakura Season", "Golden Week"],
        "related_events": ["park cherry blossom viewing", "museum visits"],
        "mobility_demand_types": ["sightseeing_route", "station_to_hotel", "private_charter"],
        "common_pain_points": ["park crowds", "station crowding", "family walking burden", "luggage lockers"],
        "crowd_risk_score": 84,
        "transfer_complexity_score": 72,
        "luggage_difficulty_score": 79,
    },
    {
        "location_id": "LOC-OSAKA",
        "location_name": "Osaka",
        "location_type": "city",
        "region": "Kansai",
        "base_related_seasons": ["Golden Week", "Chinese New Year Travel", "Summer Vacation", "Christmas and Year End"],
        "related_events": ["citywide travel", "shopping and food district movement"],
        "mobility_demand_types": ["airport_transfer", "station_to_hotel", "private_charter", "family_trip"],
        "common_pain_points": ["airport-to-city distance", "hotel congestion", "family luggage", "night arrival"],
        "crowd_risk_score": 82,
        "transfer_complexity_score": 78,
        "luggage_difficulty_score": 84,
    },
    {
        "location_id": "LOC-KANSAI-AIRPORT",
        "location_name": "Kansai Airport",
        "location_type": "airport",
        "region": "Osaka",
        "base_related_seasons": ["Chinese New Year Travel", "Golden Week", "Summer Vacation"],
        "related_events": ["Kansai inbound arrivals", "late-night airport transfer"],
        "mobility_demand_types": ["airport_transfer", "multi_city_transfer", "family_group_transfer", "luggage_heavy_trip"],
        "common_pain_points": ["bridge distance", "late arrival", "large luggage", "hotel transfer uncertainty"],
        "crowd_risk_score": 79,
        "transfer_complexity_score": 84,
        "luggage_difficulty_score": 89,
    },
    {
        "location_id": "LOC-KYOTO",
        "location_name": "Kyoto",
        "location_type": "city",
        "region": "Kansai",
        "base_related_seasons": ["Sakura Season", "Autumn Leaves Season", "Chinese New Year Travel", "Japan New Year"],
        "related_events": ["temple routes", "seasonal sightseeing peaks"],
        "mobility_demand_types": ["private_charter", "sightseeing_route", "station_to_hotel", "elderly_support"],
        "common_pain_points": ["crowded buses", "scattered temples", "walking burden", "station-to-hotel transfer"],
        "crowd_risk_score": 91,
        "transfer_complexity_score": 86,
        "luggage_difficulty_score": 83,
    },
    {
        "location_id": "LOC-NAGOYA",
        "location_name": "Nagoya",
        "location_type": "city",
        "region": "Chubu",
        "base_related_seasons": ["Golden Week", "Exhibitions Concerts Sports Events", "Autumn Leaves Season"],
        "related_events": ["event staging city", "Suzuka access", "future Asian Games monitoring"],
        "mobility_demand_types": ["airport_transfer", "event_pickup", "multi_city_transfer", "station_to_hotel"],
        "common_pain_points": ["event transfer timing", "airport-city transfer", "regional route planning", "group movement"],
        "crowd_risk_score": 72,
        "transfer_complexity_score": 74,
        "luggage_difficulty_score": 72,
    },
    {
        "location_id": "LOC-CHUBU-AIRPORT",
        "location_name": "Chubu Centrair Airport",
        "location_type": "airport",
        "region": "Aichi",
        "base_related_seasons": ["Exhibitions Concerts Sports Events", "Golden Week"],
        "related_events": ["Nagoya event arrivals", "Suzuka race transfers"],
        "mobility_demand_types": ["airport_transfer", "event_pickup", "multi_city_transfer"],
        "common_pain_points": ["regional transfer uncertainty", "race weekend luggage", "airport-to-venue distance"],
        "crowd_risk_score": 70,
        "transfer_complexity_score": 78,
        "luggage_difficulty_score": 80,
    },
    {
        "location_id": "LOC-SUZUKA",
        "location_name": "Suzuka Circuit",
        "location_type": "racing_venue",
        "region": "Mie",
        "base_related_seasons": ["Exhibitions Concerts Sports Events"],
        "related_events": ["F1 / racing", "motorsport race weekend"],
        "mobility_demand_types": ["event_pickup", "private_charter", "group_transfer", "night_return"],
        "common_pain_points": ["venue exit congestion", "last-mile transfer", "late return", "group pickup confusion"],
        "crowd_risk_score": 90,
        "transfer_complexity_score": 89,
        "luggage_difficulty_score": 70,
    },
    {
        "location_id": "LOC-MOUNT-FUJI",
        "location_name": "Mount Fuji",
        "location_type": "attraction",
        "region": "Yamanashi / Shizuoka",
        "base_related_seasons": ["Summer Vacation", "Autumn Leaves Season", "Long Weekends"],
        "related_events": ["Fuji sightseeing", "seasonal day trips"],
        "mobility_demand_types": ["private_charter", "sightseeing_route", "family_trip", "elderly_support"],
        "common_pain_points": ["long day-trip route", "weather changes", "public transport complexity", "elderly walking burden"],
        "crowd_risk_score": 79,
        "transfer_complexity_score": 87,
        "luggage_difficulty_score": 74,
    },
    {
        "location_id": "LOC-SAPPORO",
        "location_name": "Sapporo",
        "location_type": "city",
        "region": "Hokkaido",
        "base_related_seasons": ["Summer Vacation", "Christmas and Year End", "School Holidays", "Golden Week"],
        "related_events": ["winter travel", "summer escape travel"],
        "mobility_demand_types": ["airport_transfer", "winter_transfer", "family_trip", "private_charter"],
        "common_pain_points": ["snow luggage", "winter road risk", "airport transfer timing", "family support"],
        "crowd_risk_score": 74,
        "transfer_complexity_score": 76,
        "luggage_difficulty_score": 83,
    },
    {
        "location_id": "LOC-OKINAWA",
        "location_name": "Okinawa",
        "location_type": "attraction",
        "region": "Okinawa",
        "base_related_seasons": ["Summer Vacation", "Golden Week", "School Holidays"],
        "related_events": ["island resort travel", "family summer trips"],
        "mobility_demand_types": ["airport_transfer", "family_trip", "private_charter", "resort_transfer"],
        "common_pain_points": ["rental car shortage", "family luggage", "resort distance", "heat fatigue"],
        "crowd_risk_score": 78,
        "transfer_complexity_score": 74,
        "luggage_difficulty_score": 82,
    },
    {
        "location_id": "LOC-TOKYO-BIG-SIGHT",
        "location_name": "Tokyo Big Sight",
        "location_type": "exhibition_center",
        "region": "Tokyo",
        "base_related_seasons": ["Exhibitions Concerts Sports Events"],
        "related_events": ["trade shows", "conference arrivals", "launch events"],
        "mobility_demand_types": ["event_pickup", "airport_transfer", "station_to_hotel", "group_transfer"],
        "common_pain_points": ["venue exit congestion", "group pickup coordination", "equipment luggage", "airport transfer timing"],
        "crowd_risk_score": 82,
        "transfer_complexity_score": 76,
        "luggage_difficulty_score": 78,
    },
]


class LocationDemandHeatmapEngine:
    """Build a local location-season mobility demand heatmap."""

    def __init__(self, root: str | Path = "runtime/location_demand_heatmap") -> None:
        self.root = Path(root)
        self.report_path = self.root / "LOCATION_DEMAND_HEATMAP_REPORT.json"
        self.heatmap_path = self.root / "location_heatmap.json"
        self.signals_path = self.root / "location_demand_signals.json"
        self.risk_path = self.root / "location_mobility_risk.json"
        self.summary_path = self.root / "location_heatmap_summary.json"

    def build(self, seasonal_calendar: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        if seasonal_calendar is None:
            seasonal_calendar = SeasonalDemandCalendarEngine().state().get("seasonalCalendar", [])
        heatmap = [self._build_location(item, seasonal_calendar) for item in DEFAULT_LOCATIONS]
        heatmap.sort(key=lambda item: item["demand_heat_score"], reverse=True)
        signals = self._signals(heatmap)
        risks = self._risks(heatmap)
        summary = self._summary(heatmap, seasonal_calendar)
        report = {
            "report_id": "LOCATION_DEMAND_HEATMAP_REPORT",
            "created_at": utc_now_iso(),
            "status": "location_heatmap_ready",
            "phase": "PREDICTIVE_DEMAND_INTELLIGENCE",
            "data_source": LOCATION_DATA_SOURCE,
            "locationHeatmap": heatmap,
            "locationDemandSignals": signals,
            "locationMobilityRisk": risks,
            "locationHeatmapSummary": summary,
            "safetyBoundary": "Location Demand Heatmap uses local sample and Seasonal Demand Calendar data only. It does not use real-time GPS, dispatch drivers, contact vehicles, publish content, quote prices, or call platform write APIs.",
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
        self.heatmap_path.write_text(json.dumps(report["locationHeatmap"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.signals_path.write_text(json.dumps(report["locationDemandSignals"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.risk_path.write_text(json.dumps(report["locationMobilityRisk"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.summary_path.write_text(json.dumps(report["locationHeatmapSummary"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    @staticmethod
    def _build_location(item: dict[str, Any], seasonal_calendar: list[dict[str, Any]]) -> dict[str, Any]:
        related_seasons = LocationDemandHeatmapEngine._related_seasons(item, seasonal_calendar)
        season_bonus = min(14, len(related_seasons) * 2)
        event_bonus = 8 if item.get("related_events") else 0
        base_score = round(
            item["crowd_risk_score"] * 0.35
            + item["transfer_complexity_score"] * 0.35
            + item["luggage_difficulty_score"] * 0.20
            + season_bonus
            + event_bonus
        )
        heat_score = max(0, min(100, base_score))
        hot_reason = LocationDemandHeatmapEngine._hot_reason(item, related_seasons)
        return {
            "location_id": item["location_id"],
            "location_name": item["location_name"],
            "location_type": item["location_type"],
            "region": item["region"],
            "related_seasons": related_seasons,
            "related_events": item.get("related_events", []),
            "mobility_demand_types": item.get("mobility_demand_types", []),
            "common_pain_points": item.get("common_pain_points", []),
            "crowd_risk_score": item["crowd_risk_score"],
            "transfer_complexity_score": item["transfer_complexity_score"],
            "luggage_difficulty_score": item["luggage_difficulty_score"],
            "demand_heat_score": heat_score,
            "hot_reason": hot_reason,
            "driver_vehicle_preparation_required": heat_score >= 75,
            "data_origin": "local_sample",
            "seasonal_calendar_linked": bool(seasonal_calendar),
            "real_time_crowd_data_connected": False,
            "gps_dispatch_enabled": False,
            "write_operations_enabled": False,
            "human_review_required": True,
            "updated_at": utc_now_iso(),
        }

    @staticmethod
    def _related_seasons(item: dict[str, Any], seasonal_calendar: list[dict[str, Any]]) -> list[str]:
        name = item["location_name"]
        base = set(item.get("base_related_seasons", []))
        aliases = LocationDemandHeatmapEngine._location_aliases(name)
        for season in seasonal_calendar:
            season_name = season.get("season_name", "")
            likely_locations = set(season.get("likely_locations", []))
            if name in likely_locations or aliases & likely_locations:
                base.add(season_name)
            if item["location_type"] == "airport" and {"Tokyo", "Osaka", "Nagoya"} & likely_locations:
                if name in {"Haneda Airport", "Narita Airport"} and "Tokyo" in likely_locations:
                    base.add(season_name)
                if name == "Kansai Airport" and "Osaka" in likely_locations:
                    base.add(season_name)
                if name == "Chubu Centrair Airport" and "Nagoya" in likely_locations:
                    base.add(season_name)
        return sorted(base)

    @staticmethod
    def _location_aliases(name: str) -> set[str]:
        aliases = {
            "Haneda Airport": {"Tokyo", "Haneda Airport"},
            "Narita Airport": {"Tokyo", "Narita Airport"},
            "Kansai Airport": {"Osaka", "Kansai Airport"},
            "Chubu Centrair Airport": {"Nagoya", "Chubu Centrair Airport"},
            "Suzuka Circuit": {"Suzuka Circuit", "Nagoya"},
            "Tokyo Big Sight": {"Tokyo Big Sight", "Tokyo"},
            "Mount Fuji": {"Mount Fuji", "Tokyo"},
        }
        return aliases.get(name, {name})

    @staticmethod
    def _hot_reason(item: dict[str, Any], related_seasons: list[str]) -> str:
        season_text = ", ".join(related_seasons[:3]) if related_seasons else "baseline travel demand"
        pain_text = ", ".join(item.get("common_pain_points", [])[:3])
        return f"{item['location_name']} links to {season_text}; main mobility pressure is {pain_text}."

    @staticmethod
    def _signals(heatmap: list[dict[str, Any]]) -> list[dict[str, Any]]:
        signals = []
        for index, location in enumerate(heatmap, start=1):
            if location["demand_heat_score"] < 65:
                continue
            signals.append(
                {
                    "signal_id": f"LOC-SIGNAL-{index:03d}",
                    "location_id": location["location_id"],
                    "location_name": location["location_name"],
                    "hot_reason": location["hot_reason"],
                    "related_seasons": location["related_seasons"],
                    "mobility_demand_types": location["mobility_demand_types"],
                    "demand_heat_score": location["demand_heat_score"],
                    "recommended_preparation": "prepare_driver_vehicle_capacity" if location["driver_vehicle_preparation_required"] else "monitor_only",
                    "data_source": LOCATION_DATA_SOURCE,
                    "needs_human_review": True,
                }
            )
        return signals

    @staticmethod
    def _risks(heatmap: list[dict[str, Any]]) -> list[dict[str, Any]]:
        risks = []
        for location in heatmap:
            overall = round(
                location["crowd_risk_score"] * 0.4
                + location["transfer_complexity_score"] * 0.35
                + location["luggage_difficulty_score"] * 0.25
            )
            risks.append(
                {
                    "risk_id": f"{location['location_id']}-MOBILITY-RISK",
                    "location_id": location["location_id"],
                    "location_name": location["location_name"],
                    "crowd_risk_score": location["crowd_risk_score"],
                    "transfer_complexity_score": location["transfer_complexity_score"],
                    "luggage_difficulty_score": location["luggage_difficulty_score"],
                    "overall_mobility_risk": overall,
                    "risk_level": "high" if overall >= 82 else "medium" if overall >= 70 else "watch",
                    "risk_reason": location["hot_reason"],
                    "driver_vehicle_preparation_required": location["driver_vehicle_preparation_required"],
                }
            )
        return risks

    @staticmethod
    def _summary(heatmap: list[dict[str, Any]], seasonal_calendar: list[dict[str, Any]]) -> dict[str, Any]:
        high_heat = [item for item in heatmap if item["demand_heat_score"] >= 80]
        return {
            "heatmap_ready": bool(heatmap),
            "locations": len(heatmap),
            "hot_locations": len([item for item in heatmap if item["demand_heat_score"] >= 65]),
            "location_types": sorted({item["location_type"] for item in heatmap}),
            "regions": sorted({item["region"] for item in heatmap}),
            "high_heat_locations": [item["location_name"] for item in high_heat],
            "driver_vehicle_preparation_required": [item["location_name"] for item in heatmap if item["driver_vehicle_preparation_required"]],
            "seasonal_calendar_linked": bool(seasonal_calendar),
            "seasonal_records_read": len(seasonal_calendar),
            "data_source": LOCATION_DATA_SOURCE,
            "real_time_crowd_data_connected": False,
            "gps_dispatch_enabled": False,
            "automatic_vehicle_contact_enabled": False,
            "automatic_quote_enabled": False,
            "write_operations_enabled": False,
        }


if __name__ == "__main__":
    result = LocationDemandHeatmapEngine().build()
    print(json.dumps({"status": result["status"], "summary": result["locationHeatmapSummary"]}, indent=2))
