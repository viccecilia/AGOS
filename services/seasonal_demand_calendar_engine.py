"""Seasonal demand calendar for Japan mobility demand prediction."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from services.runtime_persistence import utc_now_iso


SEASONAL_DATA_SOURCE = "local_sample_and_manual_import_ready"
SUPPORTED_IMPORT_MODES = ["manual_import", "csv", "json", "future_google_trends_api"]


DEFAULT_SEASONS = [
    {
        "season_id": "SEASON-SAKURA",
        "season_name": "Sakura Season",
        "time_window": "mid_March_to_early_April",
        "target_markets": ["US", "Europe", "Korea", "Taiwan", "Southeast Asia", "China"],
        "likely_locations": ["Tokyo", "Ueno", "Shinjuku", "Kyoto", "Osaka", "Mount Fuji"],
        "demand_keywords": [
            "Japan cherry blossom travel",
            "Tokyo airport transfer sakura",
            "Kyoto cherry blossom private tour",
            "Tokyo luggage transfer cherry blossom",
        ],
        "mobility_pain_points": ["crowded trains", "large luggage", "first Japan trip anxiety", "hotel transfer confusion"],
        "predicted_demand_types": ["airport_transfer", "private_charter", "family_trip", "luggage_heavy_trip"],
        "monitoring_frequency": "weekly_until_peak_then_daily",
        "risk_notes": "High crowd pressure around parks and stations; all demand signals require human review before action.",
    },
    {
        "season_id": "SEASON-GOLDEN-WEEK",
        "season_name": "Golden Week",
        "time_window": "late_April_to_early_May",
        "target_markets": ["Japan domestic", "Korea", "Taiwan", "Southeast Asia"],
        "likely_locations": ["Tokyo", "Osaka", "Kyoto", "Sapporo", "Okinawa", "Nagoya"],
        "demand_keywords": [
            "Japan Golden Week travel",
            "Golden Week airport pickup",
            "Osaka airport pickup Golden Week",
            "Japan family trip Golden Week",
        ],
        "mobility_pain_points": ["hotel surge", "crowded public transport", "family travel load", "airport queue uncertainty"],
        "predicted_demand_types": ["airport_transfer", "family_trip", "multi_city_transfer", "station_to_hotel"],
        "monitoring_frequency": "weekly_until_peak_then_daily",
        "risk_notes": "Domestic and inbound traffic overlap; avoid marking sample interest as confirmed bookings.",
    },
    {
        "season_id": "SEASON-SUMMER",
        "season_name": "Summer Vacation",
        "time_window": "July_to_August",
        "target_markets": ["US", "Europe", "Korea", "Taiwan", "Southeast Asia", "China"],
        "likely_locations": ["Tokyo", "Osaka", "Kyoto", "Mount Fuji", "Sapporo", "Okinawa"],
        "demand_keywords": [
            "Japan summer family trip",
            "Japan summer airport transfer",
            "Okinawa family private transfer",
            "Mount Fuji summer charter",
        ],
        "mobility_pain_points": ["heat fatigue", "children and elderly support", "long walking distance", "large luggage"],
        "predicted_demand_types": ["family_trip", "elderly_support", "private_charter", "sightseeing_route"],
        "monitoring_frequency": "weekly",
        "risk_notes": "Heat and family support needs can create higher private mobility demand.",
    },
    {
        "season_id": "SEASON-AUTUMN-LEAVES",
        "season_name": "Autumn Leaves Season",
        "time_window": "October_to_late_November",
        "target_markets": ["US", "Europe", "Korea", "Taiwan", "Southeast Asia", "China"],
        "likely_locations": ["Kyoto", "Mount Fuji", "Tokyo", "Osaka", "Nagoya"],
        "demand_keywords": [
            "Kyoto autumn leaves",
            "Japan autumn leaves private tour",
            "Mount Fuji autumn charter",
            "Kyoto luggage transfer autumn",
        ],
        "mobility_pain_points": ["scattered sightseeing routes", "crowded buses", "station to temple transfer", "elderly walking burden"],
        "predicted_demand_types": ["private_charter", "sightseeing_route", "elderly_support", "station_to_hotel"],
        "monitoring_frequency": "weekly_until_peak_then_daily",
        "risk_notes": "Kyoto and Fuji routes can be congested; driver wait-time risk should be surfaced later.",
    },
    {
        "season_id": "SEASON-CHRISTMAS",
        "season_name": "Christmas and Year End",
        "time_window": "mid_December_to_late_December",
        "target_markets": ["US", "Europe", "Korea", "Taiwan", "Southeast Asia"],
        "likely_locations": ["Tokyo", "Shibuya", "Shinjuku", "Osaka", "Sapporo"],
        "demand_keywords": [
            "Japan Christmas travel",
            "Tokyo Christmas airport transfer",
            "Shibuya Christmas hotel transfer",
            "Sapporo winter airport pickup",
        ],
        "mobility_pain_points": ["night arrival", "winter luggage", "hotel district congestion", "late train anxiety"],
        "predicted_demand_types": ["airport_transfer", "night_arrival", "station_to_hotel", "luggage_heavy_trip"],
        "monitoring_frequency": "weekly",
        "risk_notes": "Night and winter transfer demand needs stronger local confirmation before scaling.",
    },
    {
        "season_id": "SEASON-CHINESE-NEW-YEAR",
        "season_name": "Chinese New Year Travel",
        "time_window": "late_January_to_mid_February",
        "target_markets": ["China", "Taiwan", "Hong Kong", "Southeast Asia"],
        "likely_locations": ["Tokyo", "Osaka", "Kyoto", "Haneda Airport", "Narita Airport", "Kansai Airport"],
        "demand_keywords": [
            "Japan Chinese New Year travel",
            "Tokyo airport transfer Chinese New Year",
            "Osaka airport pickup Chinese New Year",
            "Japan family charter Chinese New Year",
        ],
        "mobility_pain_points": ["family group transfer", "airport arrival peaks", "large luggage", "language support"],
        "predicted_demand_types": ["airport_transfer", "family_trip", "private_charter", "luggage_heavy_trip"],
        "monitoring_frequency": "weekly_until_peak_then_daily",
        "risk_notes": "Inbound family group demand may rise quickly; do not treat keyword interest as confirmed orders.",
    },
    {
        "season_id": "SEASON-JAPAN-NEW-YEAR",
        "season_name": "Japan New Year",
        "time_window": "late_December_to_early_January",
        "target_markets": ["Japan domestic", "US", "Europe", "Korea", "Taiwan"],
        "likely_locations": ["Tokyo", "Kyoto", "Osaka", "Nagoya", "Sapporo"],
        "demand_keywords": [
            "Japan New Year travel",
            "Tokyo New Year airport transfer",
            "Kyoto New Year shrine visit",
            "Japan holiday transport",
        ],
        "mobility_pain_points": ["holiday timetable changes", "late night movement", "station crowding", "family luggage"],
        "predicted_demand_types": ["airport_transfer", "night_arrival", "private_charter", "station_to_hotel"],
        "monitoring_frequency": "weekly",
        "risk_notes": "Holiday timetable and crowd changes need verified local source checks.",
    },
    {
        "season_id": "SEASON-LONG-WEEKENDS",
        "season_name": "Long Weekends",
        "time_window": "rolling_three_day_weekends",
        "target_markets": ["Japan domestic", "Korea", "Taiwan"],
        "likely_locations": ["Tokyo", "Osaka", "Kyoto", "Nagoya", "Mount Fuji"],
        "demand_keywords": [
            "Japan long weekend travel",
            "Tokyo weekend private tour",
            "Mount Fuji weekend charter",
            "Osaka weekend airport pickup",
        ],
        "mobility_pain_points": ["short trip density", "same-day luggage", "station crowding", "limited planning time"],
        "predicted_demand_types": ["private_charter", "sightseeing_route", "station_to_hotel", "airport_transfer"],
        "monitoring_frequency": "weekly",
        "risk_notes": "Rolling holiday windows should be refreshed by local calendar data before operational use.",
    },
    {
        "season_id": "SEASON-SCHOOL-HOLIDAYS",
        "season_name": "School Holidays",
        "time_window": "spring_summer_winter_school_breaks",
        "target_markets": ["Japan domestic", "US", "Europe", "Korea", "Taiwan", "Southeast Asia"],
        "likely_locations": ["Tokyo", "Osaka", "Okinawa", "Sapporo", "Mount Fuji"],
        "demand_keywords": [
            "Japan school holiday family trip",
            "Japan family airport transfer",
            "Okinawa family transfer",
            "Tokyo family luggage transfer",
        ],
        "mobility_pain_points": ["children support", "stroller and luggage", "elderly support", "rain and heat backup"],
        "predicted_demand_types": ["family_trip", "elderly_support", "luggage_heavy_trip", "private_charter"],
        "monitoring_frequency": "monthly_then_weekly_near_breaks",
        "risk_notes": "School break windows vary by country and region; treat this as monitoring structure.",
    },
    {
        "season_id": "SEASON-EVENTS",
        "season_name": "Exhibitions Concerts Sports Events",
        "time_window": "event_driven",
        "target_markets": ["Japan domestic", "US", "Europe", "Korea", "Taiwan", "China"],
        "likely_locations": ["Tokyo Big Sight", "Makuhari Messe", "Nagoya", "Suzuka Circuit", "Osaka", "Kyoto"],
        "demand_keywords": [
            "Japan event transfer",
            "Suzuka Circuit transfer",
            "Tokyo Big Sight taxi alternative",
            "Nagoya event airport pickup",
        ],
        "mobility_pain_points": ["venue exit congestion", "event pickup confusion", "late return", "group movement"],
        "predicted_demand_types": ["event_pickup", "private_charter", "station_to_hotel", "night_arrival"],
        "monitoring_frequency": "event_calendar_weekly_then_daily_near_event",
        "risk_notes": "Event signals must be verified against official event dates before commercial action.",
    },
]


class SeasonalDemandCalendarEngine:
    """Build a local seasonal demand calendar and monitoring plan."""

    def __init__(self, root: str | Path = "runtime/seasonal_demand_calendar") -> None:
        self.root = Path(root)
        self.report_path = self.root / "SEASONAL_DEMAND_CALENDAR_REPORT.json"
        self.calendar_path = self.root / "seasonal_calendar.json"
        self.keywords_path = self.root / "seasonal_keywords.json"
        self.monitoring_plan_path = self.root / "seasonal_monitoring_plan.json"
        self.summary_path = self.root / "seasonal_demand_summary.json"

    def build(self, imports: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        seasons = self._merge_imports(DEFAULT_SEASONS, imports or [])
        keywords = self._keywords(seasons)
        monitoring_plan = self._monitoring_plan(seasons)
        summary = self._summary(seasons, keywords, monitoring_plan)
        report = {
            "report_id": "SEASONAL_DEMAND_CALENDAR_REPORT",
            "created_at": utc_now_iso(),
            "status": "seasonal_calendar_ready",
            "phase": "PREDICTIVE_DEMAND_INTELLIGENCE",
            "data_source": SEASONAL_DATA_SOURCE,
            "supportedImportModes": SUPPORTED_IMPORT_MODES,
            "seasonalCalendar": seasons,
            "seasonalKeywords": keywords,
            "seasonalMonitoringPlan": monitoring_plan,
            "seasonalDemandSummary": summary,
            "safetyBoundary": "Seasonal Demand Calendar uses local sample/manual-import-ready planning data only. It does not call Google Trends, scrape login-only data, post, reply, contact customers, dispatch drivers, or call platform write APIs.",
        }
        self.persist(report)
        return report

    def build_from_json(self, path: str | Path) -> dict[str, Any]:
        imports = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(imports, list):
            raise ValueError("JSON import must be a list of season records")
        return self.build(imports)

    def build_from_csv(self, path: str | Path) -> dict[str, Any]:
        with Path(path).open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        imports = []
        for row in rows:
            imports.append(
                {
                    "season_id": row.get("season_id", ""),
                    "season_name": row.get("season_name", ""),
                    "time_window": row.get("time_window", ""),
                    "target_markets": self._split(row.get("target_markets", "")),
                    "likely_locations": self._split(row.get("likely_locations", "")),
                    "demand_keywords": self._split(row.get("demand_keywords", "")),
                    "mobility_pain_points": self._split(row.get("mobility_pain_points", "")),
                    "predicted_demand_types": self._split(row.get("predicted_demand_types", "")),
                    "monitoring_frequency": row.get("monitoring_frequency", "manual_review"),
                    "risk_notes": row.get("risk_notes", "Manual import requires human review."),
                }
            )
        return self.build(imports)

    def state(self) -> dict[str, Any]:
        if self.report_path.exists():
            return json.loads(self.report_path.read_text(encoding="utf-8"))
        return self.build()

    def persist(self, report: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.calendar_path.write_text(json.dumps(report["seasonalCalendar"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.keywords_path.write_text(json.dumps(report["seasonalKeywords"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.monitoring_plan_path.write_text(json.dumps(report["seasonalMonitoringPlan"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.summary_path.write_text(json.dumps(report["seasonalDemandSummary"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    @staticmethod
    def _merge_imports(defaults: list[dict[str, Any]], imports: list[dict[str, Any]]) -> list[dict[str, Any]]:
        by_id = {item["season_id"]: dict(item, data_origin="local_sample") for item in defaults}
        for item in imports:
            season_id = item.get("season_id")
            if not season_id:
                continue
            merged = dict(by_id.get(season_id, {}))
            merged.update(item)
            merged["data_origin"] = item.get("data_origin", "manual_import")
            by_id[season_id] = merged
        return [SeasonalDemandCalendarEngine._normalize_record(item) for item in by_id.values()]

    @staticmethod
    def _normalize_record(item: dict[str, Any]) -> dict[str, Any]:
        required_list_fields = [
            "target_markets",
            "likely_locations",
            "demand_keywords",
            "mobility_pain_points",
            "predicted_demand_types",
        ]
        normalized = dict(item)
        for field in required_list_fields:
            value = normalized.get(field, [])
            normalized[field] = value if isinstance(value, list) else SeasonalDemandCalendarEngine._split(str(value))
        normalized.setdefault("monitoring_frequency", "manual_review")
        normalized.setdefault("risk_notes", "Requires human review before operational use.")
        normalized.setdefault("data_origin", "local_sample")
        normalized["real_api_connected"] = False
        normalized["human_review_required"] = True
        normalized["write_operations_enabled"] = False
        normalized["updated_at"] = utc_now_iso()
        return normalized

    @staticmethod
    def _keywords(seasons: list[dict[str, Any]]) -> list[dict[str, Any]]:
        records = []
        for season in seasons:
            for index, keyword in enumerate(season.get("demand_keywords", []), start=1):
                records.append(
                    {
                        "keyword_id": f"{season['season_id']}-KW-{index:03d}",
                        "season_id": season["season_id"],
                        "season_name": season["season_name"],
                        "keyword": keyword,
                        "monitoring_channels": ["Google Trends structure", "manual import", "CSV", "JSON", "future API"],
                        "target_markets": season.get("target_markets", []),
                        "likely_locations": season.get("likely_locations", []),
                        "data_origin": season.get("data_origin", "local_sample"),
                        "real_google_trends_connected": False,
                        "human_review_required": True,
                    }
                )
        return records

    @staticmethod
    def _monitoring_plan(seasons: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "plan_id": f"{season['season_id']}-MONITOR",
                "season_id": season["season_id"],
                "season_name": season["season_name"],
                "time_window": season["time_window"],
                "monitoring_frequency": season["monitoring_frequency"],
                "keyword_count": len(season.get("demand_keywords", [])),
                "input_modes": SUPPORTED_IMPORT_MODES,
                "data_source_status": season.get("data_origin", "local_sample"),
                "google_trends_api_required_now": False,
                "future_api_hook": "reserved",
                "review_gate": "needs_human_review",
            }
            for season in seasons
        ]

    @staticmethod
    def _summary(
        seasons: list[dict[str, Any]],
        keywords: list[dict[str, Any]],
        monitoring_plan: list[dict[str, Any]],
    ) -> dict[str, Any]:
        focus = seasons[0] if seasons else {}
        upcoming = [
            season["season_name"]
            for season in seasons
            if season.get("monitoring_frequency") in {"weekly_until_peak_then_daily", "event_calendar_weekly_then_daily_near_event"}
        ]
        return {
            "calendar_ready": bool(seasons),
            "seasons": len(seasons),
            "keywords": len(keywords),
            "monitoring_plans": len(monitoring_plan),
            "current_focus_season": focus.get("season_name", "none"),
            "upcoming_peak_seasons": upcoming,
            "target_markets": sorted({market for season in seasons for market in season.get("target_markets", [])}),
            "likely_locations": sorted({location for season in seasons for location in season.get("likely_locations", [])}),
            "predicted_demand_types": sorted({demand for season in seasons for demand in season.get("predicted_demand_types", [])}),
            "data_source": SEASONAL_DATA_SOURCE,
            "real_google_trends_api_connected": False,
            "manual_import_supported": True,
            "csv_import_supported": True,
            "json_import_supported": True,
            "write_operations_enabled": False,
        }

    @staticmethod
    def _split(value: str) -> list[str]:
        return [item.strip() for item in value.replace("|", ",").split(",") if item.strip()]


if __name__ == "__main__":
    result = SeasonalDemandCalendarEngine().build()
    print(json.dumps({"status": result["status"], "summary": result["seasonalDemandSummary"]}, indent=2))
