"""Event intelligence engine for short-term demand spike analysis."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from services.runtime_persistence import utc_now_iso
from services.spatial_intelligence_engine import SpatialIntelligenceEngine


DEFAULT_SPATIAL_INTELLIGENCE_PATH = Path("runtime/spatial_intelligence/spatial_intelligence.json")
DEFAULT_OUTPUT_DIR = Path("runtime/event_intelligence")

SUPPORTED_EVENT_TYPES = [
    "concert",
    "sports event",
    "exhibition",
    "conference",
    "festival",
    "race",
    "product launch",
    "school holiday",
    "public holiday",
]

DEFAULT_EVENTS: list[dict[str, Any]] = [
    {
        "event_id": "EVENT-SUZUKA-RACE-WEEKEND",
        "event_name": "Suzuka Race Weekend",
        "event_type": "race",
        "market": "US",
        "location": "Suzuka Circuit",
        "time_window": "event_weekend_sample_window",
        "related_keywords": ["Suzuka Circuit transfer", "F1 Japan race pickup", "Nagoya to Suzuka private transfer"],
        "source_type": "sample_event_catalog",
    },
    {
        "event_id": "EVENT-TOKYO-BIG-SIGHT-EXPO",
        "event_name": "Tokyo Big Sight Trade Expo",
        "event_type": "exhibition",
        "market": "Taiwan",
        "location": "Tokyo Big Sight",
        "time_window": "three_day_exhibition_sample_window",
        "related_keywords": ["Tokyo Big Sight transfer", "expo airport pickup", "conference luggage transfer"],
        "source_type": "sample_event_catalog",
    },
    {
        "event_id": "EVENT-NAGOYA-PRODUCT-LAUNCH",
        "event_name": "Nagoya Product Launch Week",
        "event_type": "product launch",
        "market": "Korea",
        "location": "Nagoya",
        "time_window": "launch_week_sample_window",
        "related_keywords": ["Nagoya product launch transfer", "Chubu airport event pickup", "business travel Nagoya"],
        "source_type": "sample_event_catalog",
    },
    {
        "event_id": "EVENT-KYOTO-AUTUMN-FESTIVAL",
        "event_name": "Kyoto Autumn Festival Cluster",
        "event_type": "festival",
        "market": "Taiwan",
        "location": "Kyoto",
        "time_window": "autumn_peak_sample_window",
        "related_keywords": ["Kyoto autumn festival transfer", "Kyoto temple crowd", "private charter Kyoto autumn"],
        "source_type": "sample_event_catalog",
    },
    {
        "event_id": "EVENT-TOKYO-CONCERT-NIGHT",
        "event_name": "Tokyo Concert Night Sample",
        "event_type": "concert",
        "market": "US",
        "location": "Tokyo",
        "time_window": "single_night_concert_sample_window",
        "related_keywords": ["Tokyo concert night transfer", "late night hotel transfer", "Tokyo event pickup"],
        "source_type": "sample_event_catalog",
    },
    {
        "event_id": "EVENT-GOLDEN-WEEK-PUBLIC-HOLIDAY",
        "event_name": "Golden Week Public Holiday Surge",
        "event_type": "public holiday",
        "market": "Korea",
        "location": "Osaka",
        "time_window": "golden_week_sample_window",
        "related_keywords": ["Golden Week airport pickup", "Osaka family transfer", "public holiday hotel transfer"],
        "source_type": "sample_event_catalog",
    },
    {
        "event_id": "EVENT-SCHOOL-HOLIDAY-OKINAWA",
        "event_name": "Okinawa School Holiday Family Travel",
        "event_type": "school holiday",
        "market": "Southeast Asia",
        "location": "Okinawa",
        "time_window": "summer_school_holiday_sample_window",
        "related_keywords": ["Okinawa family transfer", "school holiday Japan family trip", "resort airport transfer"],
        "source_type": "sample_event_catalog",
    },
    {
        "event_id": "EVENT-SAPPORO-WINTER-SPORTS",
        "event_name": "Sapporo Winter Sports Travel",
        "event_type": "sports event",
        "market": "Taiwan",
        "location": "Sapporo",
        "time_window": "winter_sports_sample_window",
        "related_keywords": ["Sapporo winter transfer", "snow luggage airport pickup", "winter sports hotel transfer"],
        "source_type": "sample_event_catalog",
    },
    {
        "event_id": "EVENT-TOKYO-BUSINESS-CONFERENCE",
        "event_name": "Tokyo Business Conference Arrival",
        "event_type": "conference",
        "market": "Europe",
        "location": "Tokyo",
        "time_window": "conference_arrival_sample_window",
        "related_keywords": ["Tokyo conference airport transfer", "business district hotel transfer", "conference luggage pickup"],
        "source_type": "sample_event_catalog",
    },
]

EVENT_TYPE_DEMAND = {
    "concert": ["night_arrival", "event_pickup", "station_to_hotel"],
    "sports event": ["event_pickup", "group_transfer", "private_charter"],
    "exhibition": ["event_pickup", "airport_transfer", "equipment_luggage"],
    "conference": ["airport_transfer", "business_transfer", "station_to_hotel"],
    "festival": ["private_charter", "sightseeing_route", "elderly_support"],
    "race": ["event_pickup", "private_charter", "group_transfer", "night_return"],
    "product launch": ["airport_transfer", "business_transfer", "event_pickup"],
    "school holiday": ["family_trip", "airport_transfer", "luggage_heavy_trip"],
    "public holiday": ["airport_transfer", "family_trip", "station_to_hotel"],
}


class EventIntelligenceEngine:
    """Build event-driven short-term demand spike intelligence."""

    def __init__(
        self,
        spatial_intelligence_path: str | Path = DEFAULT_SPATIAL_INTELLIGENCE_PATH,
        output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    ) -> None:
        self.spatial_intelligence_path = Path(spatial_intelligence_path)
        self.output_dir = Path(output_dir)
        self.report_path = self.output_dir / "EVENT_INTELLIGENCE_REPORT.json"
        self.event_path = self.output_dir / "event_intelligence.json"
        self.heatmap_path = self.output_dir / "event_location_heatmap.json"
        self.mobility_path = self.output_dir / "event_mobility_demand.json"
        self.summary_path = self.output_dir / "event_intelligence_summary.json"

    def build(
        self,
        spatial_intelligence: list[dict[str, Any]] | None = None,
        events: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        spatial = spatial_intelligence if spatial_intelligence is not None else self._load_spatial_intelligence()
        source_events = events if events is not None else DEFAULT_EVENTS
        event_intelligence = [self._event_item(item, spatial, index) for index, item in enumerate(source_events, start=1)]
        event_location_heatmap = self._event_location_heatmap(event_intelligence)
        event_mobility_demand = self._event_mobility_demand(event_intelligence)
        summary = self._summary(event_intelligence, event_location_heatmap, event_mobility_demand)
        report = {
            "report_id": "EVENT_INTELLIGENCE_REPORT",
            "round_id": "ROUND-GLOBAL-009",
            "created_at": utc_now_iso(),
            "status": "event_intelligence_ready",
            "phase": "GLOBAL_PREDICTIVE_INTELLIGENCE",
            "supportedEventTypes": SUPPORTED_EVENT_TYPES,
            "eventIntelligence": event_intelligence,
            "eventLocationHeatmap": event_location_heatmap,
            "eventMobilityDemand": event_mobility_demand,
            "eventIntelligenceSummary": summary,
            "safetyBoundary": "Event Intelligence Engine uses sample/read-only event structures to estimate short-term demand spikes only. It does not mark sample events as real happened events, contact merchants, contact drivers, dispatch vehicles, publish, reply, or call platform write APIs.",
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
        self.event_path.write_text(json.dumps(report["eventIntelligence"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.heatmap_path.write_text(json.dumps(report["eventLocationHeatmap"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.mobility_path.write_text(json.dumps(report["eventMobilityDemand"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.summary_path.write_text(json.dumps(report["eventIntelligenceSummary"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    def _load_spatial_intelligence(self) -> list[dict[str, Any]]:
        if not self.spatial_intelligence_path.exists():
            SpatialIntelligenceEngine().build()
        payload = json.loads(self.spatial_intelligence_path.read_text(encoding="utf-8")) if self.spatial_intelligence_path.exists() else []
        return payload if isinstance(payload, list) else []

    @classmethod
    def _event_item(cls, event: dict[str, Any], spatial: list[dict[str, Any]], index: int) -> dict[str, Any]:
        spatial_rows = cls._matching_spatial(event, spatial)
        best_spatial = spatial_rows[0] if spatial_rows else {}
        mobility = cls._likely_mobility_demand(event, best_spatial)
        crowd_pressure = cls._crowd_pressure(event, best_spatial, len(spatial_rows))
        confidence = cls._confidence_score(event, best_spatial, len(spatial_rows))
        return {
            "event_id": event.get("event_id", f"EVENT-SAMPLE-{index:03d}"),
            "event_name": event.get("event_name", "Sample Event"),
            "event_type": event.get("event_type", "needs_review"),
            "market": event.get("market", best_spatial.get("market", "needs_review")),
            "location": event.get("location", best_spatial.get("location_name", "needs_review")),
            "time_window": event.get("time_window", "sample_event_window"),
            "expected_crowd_pressure": crowd_pressure,
            "likely_mobility_demand": mobility,
            "related_keywords": event.get("related_keywords", []),
            "source_type": event.get("source_type", "sample_event_catalog"),
            "confidence_score": confidence,
            "human_review_required": True,
            "sample_event_only": True,
            "real_event_confirmed": False,
            "event_happened": False,
            "source_spatial_location_ids": [item.get("location_id", "") for item in spatial_rows[:3]],
            "risk_notes": cls._risk_notes(event, best_spatial),
            "auto_merchant_contact_allowed": False,
            "auto_driver_contact_allowed": False,
            "gps_dispatch_enabled": False,
            "auto_publish_allowed": False,
            "auto_reply_allowed": False,
            "write_api_allowed": False,
        }

    @staticmethod
    def _matching_spatial(event: dict[str, Any], spatial: list[dict[str, Any]]) -> list[dict[str, Any]]:
        location = event.get("location", "")
        market = event.get("market", "")
        rows = [
            item
            for item in spatial
            if item.get("location_name") == location and (item.get("market") == market or not market)
        ]
        if not rows:
            rows = [item for item in spatial if item.get("location_name") == location]
        return sorted(rows, key=lambda item: item.get("demand_heat_score", 0), reverse=True)

    @staticmethod
    def _likely_mobility_demand(event: dict[str, Any], spatial: dict[str, Any]) -> list[str]:
        values = list(EVENT_TYPE_DEMAND.get(event.get("event_type", ""), []))
        values.extend(spatial.get("mobility_demand_types", []))
        return list(dict.fromkeys(values))[:8]

    @staticmethod
    def _crowd_pressure(event: dict[str, Any], spatial: dict[str, Any], match_count: int) -> int:
        base = int(spatial.get("crowd_pressure_score", spatial.get("demand_heat_score", 62)))
        event_bonus = {
            "race": 12,
            "concert": 10,
            "sports event": 10,
            "exhibition": 8,
            "conference": 6,
            "festival": 9,
            "product launch": 6,
            "school holiday": 8,
            "public holiday": 10,
        }.get(event.get("event_type", ""), 4)
        return max(0, min(100, base + event_bonus + min(6, match_count)))

    @staticmethod
    def _confidence_score(event: dict[str, Any], spatial: dict[str, Any], match_count: int) -> int:
        spatial_conf = int(spatial.get("confidence_score", 45))
        keyword_bonus = min(10, len(event.get("related_keywords", [])) * 2)
        match_bonus = min(8, match_count * 2)
        return max(20, min(82, round(spatial_conf * 0.75 + keyword_bonus + match_bonus)))

    @staticmethod
    def _risk_notes(event: dict[str, Any], spatial: dict[str, Any]) -> str:
        return (
            f"{event.get('event_name')} is sample-only. Location heat is {spatial.get('demand_heat_score', 'unknown')} "
            f"at {event.get('location')}; verify official event dates and venue logistics before any business action."
        )

    @staticmethod
    def _event_location_heatmap(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "event_id": item["event_id"],
                "event_name": item["event_name"],
                "event_type": item["event_type"],
                "location": item["location"],
                "market": item["market"],
                "expected_crowd_pressure": item["expected_crowd_pressure"],
                "confidence_score": item["confidence_score"],
                "human_review_required": item["human_review_required"],
                "sample_event_only": item["sample_event_only"],
            }
            for item in sorted(events, key=lambda row: row["expected_crowd_pressure"], reverse=True)
        ]

    @staticmethod
    def _event_mobility_demand(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        heat: Counter[str] = Counter()
        count: Counter[str] = Counter()
        event_types: dict[str, set[str]] = {}
        for item in events:
            for demand_type in item.get("likely_mobility_demand", []):
                heat[demand_type] += item.get("expected_crowd_pressure", 0)
                count[demand_type] += 1
                event_types.setdefault(demand_type, set()).add(item.get("event_type", "needs_review"))
        return [
            {
                "demand_type": demand_type,
                "event_count": count[demand_type],
                "average_event_pressure": round(heat[demand_type] / max(1, count[demand_type]), 2),
                "event_types": sorted(event_types.get(demand_type, set())),
                "human_review_required": True,
                "auto_merchant_contact_allowed": False,
                "auto_driver_contact_allowed": False,
            }
            for demand_type, _ in heat.most_common()
        ]

    @staticmethod
    def _summary(
        events: list[dict[str, Any]],
        heatmap: list[dict[str, Any]],
        mobility: list[dict[str, Any]],
    ) -> dict[str, Any]:
        return {
            "event_intelligence_ready": True,
            "event_count": len(events),
            "event_type_count": len({item["event_type"] for item in events}),
            "location_count": len({item["location"] for item in events}),
            "market_count": len({item["market"] for item in events}),
            "heatmap_rows": len(heatmap),
            "mobility_demand_count": len(mobility),
            "supported_event_types": SUPPORTED_EVENT_TYPES,
            "top_event_pressure": heatmap[:6],
            "sample_event_only": True,
            "real_events_confirmed": False,
            "event_happened_marked_true": False,
            "all_items_human_review_required": all(item["human_review_required"] for item in events),
            "auto_merchant_contact_allowed": False,
            "auto_driver_contact_allowed": False,
            "gps_dispatch_enabled": False,
            "auto_publish_allowed": False,
            "auto_reply_allowed": False,
            "write_api_allowed": False,
            "next_recommendation": "Use reviewed event intelligence as input for Mobility Intelligence Engine; verify official event dates before any operational action.",
        }
