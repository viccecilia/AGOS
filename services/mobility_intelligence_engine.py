"""Mobility intelligence engine for real demand judgment."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.event_intelligence_engine import EventIntelligenceEngine
from services.intelligence_ranking_noise_filter import IntelligenceRankingNoiseFilter
from services.mobility_demand_intent_engine import MobilityDemandIntentEngine
from services.runtime_persistence import utc_now_iso
from services.seasonal_intelligence_engine import SeasonalIntelligenceEngine
from services.spatial_intelligence_engine import SpatialIntelligenceEngine


DEFAULT_SEASONAL_INTELLIGENCE_PATH = Path("runtime/seasonal_intelligence/seasonal_intelligence.json")
DEFAULT_SPATIAL_INTELLIGENCE_PATH = Path("runtime/spatial_intelligence/spatial_intelligence.json")
DEFAULT_EVENT_INTELLIGENCE_PATH = Path("runtime/event_intelligence/event_intelligence.json")
DEFAULT_MOBILITY_INTENTS_PATH = Path("runtime/mobility_demand_intent/mobility_intents.json")
DEFAULT_RANKED_INTELLIGENCE_PATH = Path("runtime/intelligence_ranking/ranked_intelligence.json")
DEFAULT_OUTPUT_DIR = Path("runtime/mobility_intelligence")

SUPPORTED_MOBILITY_DEMAND = [
    "airport transfer",
    "private charter",
    "family trip",
    "elderly support",
    "luggage-heavy trip",
    "night arrival",
    "multi-city route",
    "event pickup",
    "hotel transfer",
    "sightseeing route",
    "no real mobility intent",
]

DEMAND_TYPE_ALIASES = {
    "airport_transfer": "airport transfer",
    "airport transfer": "airport transfer",
    "private_charter": "private charter",
    "private charter": "private charter",
    "family_trip": "family trip",
    "family trip": "family trip",
    "elderly_support": "elderly support",
    "elderly support": "elderly support",
    "luggage_heavy_trip": "luggage-heavy trip",
    "luggage-heavy trip": "luggage-heavy trip",
    "equipment_luggage": "luggage-heavy trip",
    "snow luggage": "luggage-heavy trip",
    "night_arrival": "night arrival",
    "night arrival": "night arrival",
    "night_return": "night arrival",
    "multi_city_transfer": "multi-city route",
    "multi-city route": "multi-city route",
    "multi city": "multi-city route",
    "event_pickup": "event pickup",
    "event pickup": "event pickup",
    "group_transfer": "event pickup",
    "station_to_hotel": "hotel transfer",
    "hotel_transfer": "hotel transfer",
    "hotel transfer": "hotel transfer",
    "business_transfer": "hotel transfer",
    "sightseeing_route": "sightseeing route",
    "sightseeing route": "sightseeing route",
    "public_transport_anxiety": "no real mobility intent",
    "price_comparison": "no real mobility intent",
    "no_real_mobility_intent": "no real mobility intent",
    "no real mobility intent": "no real mobility intent",
}


class MobilityIntelligenceEngine:
    """Judge which predictive signals are true mobility demand."""

    def __init__(
        self,
        seasonal_intelligence_path: str | Path = DEFAULT_SEASONAL_INTELLIGENCE_PATH,
        spatial_intelligence_path: str | Path = DEFAULT_SPATIAL_INTELLIGENCE_PATH,
        event_intelligence_path: str | Path = DEFAULT_EVENT_INTELLIGENCE_PATH,
        mobility_intents_path: str | Path = DEFAULT_MOBILITY_INTENTS_PATH,
        ranked_intelligence_path: str | Path = DEFAULT_RANKED_INTELLIGENCE_PATH,
        output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    ) -> None:
        self.seasonal_intelligence_path = Path(seasonal_intelligence_path)
        self.spatial_intelligence_path = Path(spatial_intelligence_path)
        self.event_intelligence_path = Path(event_intelligence_path)
        self.mobility_intents_path = Path(mobility_intents_path)
        self.ranked_intelligence_path = Path(ranked_intelligence_path)
        self.output_dir = Path(output_dir)
        self.report_path = self.output_dir / "MOBILITY_INTELLIGENCE_REPORT.json"
        self.intelligence_path = self.output_dir / "mobility_intelligence.json"
        self.high_value_path = self.output_dir / "high_value_mobility_demand.json"
        self.noise_path = self.output_dir / "mobility_noise_signals.json"
        self.summary_path = self.output_dir / "mobility_intelligence_summary.json"

    def build(
        self,
        seasonal_intelligence: list[dict[str, Any]] | None = None,
        spatial_intelligence: list[dict[str, Any]] | None = None,
        event_intelligence: list[dict[str, Any]] | None = None,
        mobility_intents: list[dict[str, Any]] | None = None,
        ranked_intelligence: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        seasonal = seasonal_intelligence if seasonal_intelligence is not None else self._load_seasonal_intelligence()
        spatial = spatial_intelligence if spatial_intelligence is not None else self._load_spatial_intelligence()
        events = event_intelligence if event_intelligence is not None else self._load_event_intelligence()
        intents = mobility_intents if mobility_intents is not None else self._load_mobility_intents()
        ranked = ranked_intelligence if ranked_intelligence is not None else self._load_ranked_intelligence()

        rows = self._mobility_rows(seasonal, spatial, events, intents, ranked)
        high_value = [
            item
            for item in rows
            if not item["noise_flag"]
            and item["demand_type"] != "no real mobility intent"
            and item["intent_strength"] >= 70
            and item["conversion_potential"] >= 62
        ]
        noise = [
            item
            for item in rows
            if item["noise_flag"] or item["demand_type"] == "no real mobility intent" or item["intent_strength"] <= 35
        ]
        summary = self._summary(rows, high_value, noise)
        report = {
            "report_id": "MOBILITY_INTELLIGENCE_REPORT",
            "round_id": "ROUND-GLOBAL-010",
            "created_at": utc_now_iso(),
            "status": "mobility_intelligence_ready",
            "phase": "GLOBAL_PREDICTIVE_INTELLIGENCE",
            "supportedMobilityDemand": SUPPORTED_MOBILITY_DEMAND,
            "mobilityIntelligence": rows,
            "highValueMobilityDemand": high_value,
            "mobilityNoiseSignals": noise,
            "mobilityIntelligenceSummary": summary,
            "safetyBoundary": "Mobility Intelligence Engine judges real mobility demand from local/sample/read-only intelligence only. It does not quote prices, dispatch vehicles, contact customers, contact drivers, publish, reply, DM, log in, or call platform write APIs.",
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
        self.intelligence_path.write_text(json.dumps(report["mobilityIntelligence"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.high_value_path.write_text(json.dumps(report["highValueMobilityDemand"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.noise_path.write_text(json.dumps(report["mobilityNoiseSignals"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.summary_path.write_text(json.dumps(report["mobilityIntelligenceSummary"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

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

    def _load_mobility_intents(self) -> list[dict[str, Any]]:
        if not self.mobility_intents_path.exists():
            MobilityDemandIntentEngine().build()
        return self._load_list(self.mobility_intents_path)

    def _load_ranked_intelligence(self) -> list[dict[str, Any]]:
        if not self.ranked_intelligence_path.exists():
            IntelligenceRankingNoiseFilter().build()
        return self._load_list(self.ranked_intelligence_path)

    @staticmethod
    def _load_list(path: Path) -> list[dict[str, Any]]:
        payload = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
        return payload if isinstance(payload, list) else []

    @classmethod
    def _mobility_rows(
        cls,
        seasonal: list[dict[str, Any]],
        spatial: list[dict[str, Any]],
        events: list[dict[str, Any]],
        intents: list[dict[str, Any]],
        ranked: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for event in events:
            rows.extend(cls._from_event(event, len(rows) + 1))
        for location in spatial[:18]:
            rows.extend(cls._from_spatial(location, len(rows) + 1))
        for season in seasonal[:16]:
            rows.extend(cls._from_seasonal(season, len(rows) + 1))
        for intent in intents:
            rows.append(cls._from_intent(intent, len(rows) + 1))
        rows.append(cls._noise_row(len(rows) + 1, ranked))

        deduped: list[dict[str, Any]] = []
        seen: set[tuple[str, str, str, str, str]] = set()
        for item in sorted(rows, key=lambda row: (row["noise_flag"], -row["intent_strength"], -row["conversion_potential"])):
            key = (item["market"], item["location"], item["event"], item["season"], item["demand_type"])
            if key in seen and not item["noise_flag"]:
                continue
            seen.add(key)
            deduped.append(dict(item, mobility_id=f"MOBILITY-INTEL-{len(deduped) + 1:04d}"))
        return deduped

    @classmethod
    def _from_event(cls, event: dict[str, Any], start_index: int) -> list[dict[str, Any]]:
        rows = []
        for offset, raw_demand in enumerate(event.get("likely_mobility_demand", [])[:4]):
            demand_type = cls._normalize_demand_type(raw_demand)
            pressure = int(event.get("expected_crowd_pressure", 0))
            confidence = int(event.get("confidence_score", 0))
            rows.append(
                cls._row(
                    mobility_id=f"MOBILITY-INTEL-{start_index + offset:04d}",
                    source_type="event_intelligence",
                    source_id=event.get("event_id", ""),
                    market=event.get("market", "needs_review"),
                    location=event.get("location", "needs_review"),
                    season=cls._season_from_event(event),
                    event=event.get("event_name", ""),
                    demand_type=demand_type,
                    intent_strength=min(100, round(pressure * 0.72 + confidence * 0.18 + 10)),
                    urgency_score=min(100, round(pressure * 0.78 + 10)),
                    conversion_potential=min(100, round(pressure * 0.54 + confidence * 0.28 + 8)),
                    recommended_route=cls._route_for(demand_type, event.get("location", "")),
                    noise_flag=False,
                    reason=f"Event pressure {pressure} at {event.get('location')} indicates reviewed {demand_type} demand candidate.",
                )
            )
        return rows

    @classmethod
    def _from_spatial(cls, location: dict[str, Any], start_index: int) -> list[dict[str, Any]]:
        rows = []
        demand_types = location.get("mobility_demand_types", [])
        if location.get("location_type") == "airport":
            demand_types = ["airport_transfer"] + demand_types
        for offset, raw_demand in enumerate(demand_types[:2]):
            demand_type = cls._normalize_demand_type(raw_demand)
            heat = int(location.get("demand_heat_score", 0))
            transfer = int(location.get("transfer_complexity_score", 0))
            luggage = int(location.get("luggage_difficulty_score", 0))
            rows.append(
                cls._row(
                    mobility_id=f"MOBILITY-INTEL-{start_index + offset:04d}",
                    source_type="spatial_intelligence",
                    source_id=location.get("location_id", ""),
                    market=location.get("market", "needs_review"),
                    location=location.get("location_name", "needs_review"),
                    season=(location.get("related_seasons") or ["needs_review"])[0],
                    event=(location.get("related_events") or ["none"])[0],
                    demand_type=demand_type,
                    intent_strength=min(100, round(heat * 0.62 + transfer * 0.24 + luggage * 0.1)),
                    urgency_score=min(100, round(heat * 0.5 + transfer * 0.2 + 8)),
                    conversion_potential=min(100, round(heat * 0.55 + int(location.get("confidence_score", 0)) * 0.25 + 8)),
                    recommended_route=cls._route_for(demand_type, location.get("location_name", "")),
                    noise_flag=False,
                    reason=f"Location heat {heat}, transfer complexity {transfer}, and luggage difficulty {luggage} indicate {demand_type} candidate.",
                )
            )
        return rows

    @classmethod
    def _from_seasonal(cls, season: dict[str, Any], start_index: int) -> list[dict[str, Any]]:
        rows = []
        for offset, raw_demand in enumerate(season.get("mobility_demand_types", [])[:2]):
            demand_type = cls._normalize_demand_type(raw_demand)
            heat = int(season.get("seasonal_heat_score", 0))
            confidence = int(season.get("confidence_score", 0))
            rows.append(
                cls._row(
                    mobility_id=f"MOBILITY-INTEL-{start_index + offset:04d}",
                    source_type="seasonal_intelligence",
                    source_id=season.get("season_id", ""),
                    market=season.get("market", "needs_review"),
                    location=(season.get("likely_locations") or ["needs_review"])[0],
                    season=season.get("season_name", "needs_review"),
                    event="seasonal_peak",
                    demand_type=demand_type,
                    intent_strength=min(100, round(heat * 0.58 + confidence * 0.22 + 8)),
                    urgency_score=min(100, round(heat * 0.48 + 10)),
                    conversion_potential=min(100, round(heat * 0.46 + confidence * 0.28 + 8)),
                    recommended_route=cls._route_for(demand_type, (season.get("likely_locations") or [""])[0]),
                    noise_flag=False,
                    reason=f"Season heat {heat} and confidence {confidence} imply reviewed {demand_type} planning signal.",
                )
            )
        return rows

    @classmethod
    def _from_intent(cls, intent: dict[str, Any], index: int) -> dict[str, Any]:
        demand_type = cls._normalize_demand_type(intent.get("demand_intent", "no_real_mobility_intent"))
        noise = demand_type == "no real mobility intent"
        return cls._row(
            mobility_id=f"MOBILITY-INTEL-{index:04d}",
            source_type="mobility_demand_intent",
            source_id=intent.get("intent_id", ""),
            market=intent.get("market", "needs_review"),
            location=intent.get("location", "needs_review"),
            season=intent.get("season", "needs_review"),
            event=intent.get("event", "none"),
            demand_type=demand_type,
            intent_strength=int(intent.get("intent_strength_score", 0)),
            urgency_score=int(intent.get("urgency_score", 0)),
            conversion_potential=int(intent.get("conversion_potential_score", 0)),
            recommended_route=intent.get("recommended_route", cls._route_for(demand_type, intent.get("location", ""))),
            noise_flag=noise,
            reason=intent.get("classification_reason", "Mobility demand intent classification imported for global review."),
        )

    @classmethod
    def _noise_row(cls, index: int, ranked: list[dict[str, Any]]) -> dict[str, Any]:
        unsafe = next((item for item in ranked if item.get("ranking_status") in {"noise", "low_value", "unsafe"}), {})
        return cls._row(
            mobility_id=f"MOBILITY-INTEL-{index:04d}",
            source_type="ranked_intelligence_noise_filter",
            source_id=unsafe.get("intelligence_id", "NOISE-SAMPLE"),
            market=unsafe.get("market", "Global English"),
            location="unknown",
            season="none",
            event="none",
            demand_type="no real mobility intent",
            intent_strength=18,
            urgency_score=8,
            conversion_potential=6,
            recommended_route="filter_out_no_action",
            noise_flag=True,
            reason=unsafe.get("noise_reason", "Low-confidence chatter or unrelated trend has no real mobility intent."),
        )

    @staticmethod
    def _row(
        mobility_id: str,
        source_type: str,
        source_id: str,
        market: str,
        location: str,
        season: str,
        event: str,
        demand_type: str,
        intent_strength: int,
        urgency_score: int,
        conversion_potential: int,
        recommended_route: str,
        noise_flag: bool,
        reason: str,
    ) -> dict[str, Any]:
        return {
            "mobility_id": mobility_id,
            "source_type": source_type,
            "source_id": source_id,
            "market": market,
            "location": location,
            "season": season,
            "event": event,
            "demand_type": demand_type,
            "intent_strength": max(0, min(100, intent_strength)),
            "urgency_score": max(0, min(100, urgency_score)),
            "conversion_potential": max(0, min(100, conversion_potential)),
            "recommended_route": recommended_route,
            "noise_flag": noise_flag,
            "judgment_reason": reason,
            "human_review_required": True,
            "sample_data_only": True,
            "auto_quote_allowed": False,
            "auto_dispatch_allowed": False,
            "auto_customer_contact_allowed": False,
            "auto_driver_contact_allowed": False,
            "auto_publish_allowed": False,
            "auto_reply_allowed": False,
            "write_api_allowed": False,
        }

    @staticmethod
    def _normalize_demand_type(value: str) -> str:
        normalized = DEMAND_TYPE_ALIASES.get(str(value).strip().lower().replace("-", "_"), "")
        if normalized:
            return normalized
        return DEMAND_TYPE_ALIASES.get(str(value).strip().lower(), "no real mobility intent")

    @staticmethod
    def _season_from_event(event: dict[str, Any]) -> str:
        mapping = {
            "public holiday": "Golden Week / Public Holiday",
            "school holiday": "School Holidays",
            "festival": "Autumn Leaves / Festival",
            "race": "Sports Event Season",
            "concert": "Concert Event Window",
            "exhibition": "Exhibition Season",
            "conference": "Conference Season",
            "product launch": "Business Event Window",
            "sports event": "Sports Event Season",
        }
        return mapping.get(event.get("event_type", ""), "event_window")

    @staticmethod
    def _route_for(demand_type: str, location: str) -> str:
        routes = {
            "airport transfer": "airport_transfer_review_route",
            "private charter": "private_charter_review_route",
            "family trip": "family_trip_support_review_route",
            "elderly support": "elderly_support_review_route",
            "luggage-heavy trip": "luggage_support_review_route",
            "night arrival": "night_arrival_review_route",
            "multi-city route": "multi_city_route_review_route",
            "event pickup": "event_pickup_review_route",
            "hotel transfer": "hotel_transfer_review_route",
            "sightseeing route": "sightseeing_route_review_route",
        }
        return routes.get(demand_type, "filter_out_no_action") + (f":{location}" if location else "")

    @staticmethod
    def _summary(
        rows: list[dict[str, Any]],
        high_value: list[dict[str, Any]],
        noise: list[dict[str, Any]],
    ) -> dict[str, Any]:
        demand_types = sorted({item["demand_type"] for item in rows})
        return {
            "mobility_intelligence_ready": True,
            "mobility_count": len(rows),
            "high_value_count": len(high_value),
            "noise_count": len(noise),
            "demand_types": demand_types,
            "airport_transfer_detected": "airport transfer" in demand_types,
            "event_pickup_detected": "event pickup" in demand_types,
            "no_real_mobility_intent_detected": "no real mobility intent" in demand_types,
            "high_value_and_noise_separated": not any(item["noise_flag"] for item in high_value),
            "all_items_human_review_required": all(item["human_review_required"] for item in rows),
            "sample_data_only": True,
            "auto_quote_allowed": False,
            "auto_dispatch_allowed": False,
            "auto_customer_contact_allowed": False,
            "auto_driver_contact_allowed": False,
            "auto_publish_allowed": False,
            "auto_reply_allowed": False,
            "write_api_allowed": False,
            "next_recommendation": "Use reviewed high-value mobility demand as input for Demand Prediction Engine; keep quotes, dispatch, customer contact, and driver contact blocked.",
        }


if __name__ == "__main__":
    result = MobilityIntelligenceEngine().build()
    print(json.dumps({"status": result["status"], "summary": result["mobilityIntelligenceSummary"]}, indent=2))
