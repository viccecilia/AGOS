"""Mobility demand intent classification for predictive demand intelligence."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from services.api_signal_normalization import APISignalNormalization
from services.live_data_normalization_pipeline import LiveDataNormalizationPipeline
from services.location_demand_heatmap_engine import LocationDemandHeatmapEngine
from services.runtime_persistence import utc_now_iso
from services.seasonal_demand_calendar_engine import SeasonalDemandCalendarEngine


SUPPORTED_INTENTS = [
    "airport_transfer",
    "private_charter",
    "family_trip",
    "elderly_support",
    "luggage_heavy_trip",
    "night_arrival",
    "multi_city_transfer",
    "event_pickup",
    "station_to_hotel",
    "sightseeing_route",
    "price_comparison",
    "public_transport_anxiety",
    "no_real_mobility_intent",
]

SUPPORTED_INPUT_SOURCES = [
    "normalized_live_data",
    "question_inbox",
    "scout_intelligence",
    "google_trends_keyword_signal",
    "local_csv",
    "local_json",
    "manual_import",
]

LOW_VALUE_REASONS = {
    "casual_chatter": ["just chatting", "random thought", "haha", "lol", "meme"],
    "spectator_interest": ["watching videos", "looks cool", "just curious", "dream trip someday"],
    "no_travel_plan": ["no plan", "not traveling", "maybe one day", "someday"],
    "no_transport_need": ["walking only", "staying at home", "no transport", "not moving"],
    "low_confidence_trend": ["viral joke", "rumor", "unverified", "low confidence"],
    "unrelated_to_mobility": ["food recipe", "anime ranking", "shopping haul", "weather only"],
}

INTENT_RULES: list[dict[str, Any]] = [
    {
        "intent": "airport_transfer",
        "keywords": ["airport", "haneda", "narita", "kansai airport", "chubu", "airport pickup", "airport transfer", "flight", "terminal"],
        "route": "airport_transfer_strategy",
        "base_strength": 86,
        "base_conversion": 82,
        "base_urgency": 78,
    },
    {
        "intent": "private_charter",
        "keywords": ["private tour", "charter", "private car", "day trip", "custom route", "driver for the day"],
        "route": "private_charter_strategy",
        "base_strength": 84,
        "base_conversion": 80,
        "base_urgency": 68,
    },
    {
        "intent": "family_trip",
        "keywords": ["family", "kids", "children", "stroller", "parents", "group"],
        "route": "family_support_strategy",
        "base_strength": 78,
        "base_conversion": 76,
        "base_urgency": 64,
    },
    {
        "intent": "elderly_support",
        "keywords": ["elderly", "senior", "grandparent", "wheelchair", "cannot walk", "walking burden"],
        "route": "elderly_support_strategy",
        "base_strength": 82,
        "base_conversion": 79,
        "base_urgency": 70,
    },
    {
        "intent": "luggage_heavy_trip",
        "keywords": ["luggage", "bags", "suitcase", "locker", "hands full", "heavy"],
        "route": "luggage_transfer_strategy",
        "base_strength": 75,
        "base_conversion": 72,
        "base_urgency": 63,
    },
    {
        "intent": "night_arrival",
        "keywords": ["late night", "midnight", "last train", "night arrival", "after 10pm", "red-eye"],
        "route": "night_arrival_strategy",
        "base_strength": 83,
        "base_conversion": 78,
        "base_urgency": 86,
    },
    {
        "intent": "multi_city_transfer",
        "keywords": ["tokyo to kyoto", "osaka to kyoto", "multi city", "between cities", "nagoya to suzuka", "transfer between"],
        "route": "multi_city_transfer_strategy",
        "base_strength": 80,
        "base_conversion": 74,
        "base_urgency": 66,
    },
    {
        "intent": "event_pickup",
        "keywords": ["event", "concert", "f1", "race", "suzuka", "big sight", "messe", "venue", "conference"],
        "route": "event_pickup_strategy",
        "base_strength": 82,
        "base_conversion": 77,
        "base_urgency": 82,
    },
    {
        "intent": "station_to_hotel",
        "keywords": ["station to hotel", "hotel transfer", "from station", "shinjuku station", "ueno station", "kyoto station"],
        "route": "station_to_hotel_strategy",
        "base_strength": 73,
        "base_conversion": 69,
        "base_urgency": 67,
    },
    {
        "intent": "sightseeing_route",
        "keywords": ["sightseeing", "route", "itinerary", "temples", "mount fuji", "kyoto temples", "day route"],
        "route": "sightseeing_route_strategy",
        "base_strength": 76,
        "base_conversion": 71,
        "base_urgency": 58,
    },
    {
        "intent": "price_comparison",
        "keywords": ["worth it", "price", "cost", "cheap", "expensive", "jr pass", "suica", "pasmo", "ic card"],
        "route": "price_comparison_content_strategy",
        "base_strength": 61,
        "base_conversion": 48,
        "base_urgency": 42,
    },
    {
        "intent": "public_transport_anxiety",
        "keywords": ["subway confusing", "train confusing", "transport anxiety", "getting lost", "wrong train", "public transport"],
        "route": "public_transport_anxiety_reply_strategy",
        "base_strength": 66,
        "base_conversion": 52,
        "base_urgency": 50,
    },
]

DEFAULT_MANUAL_INPUTS = [
    {
        "source_id": "MANUAL-INTENT-001",
        "source_type": "manual_import",
        "platform": "Reddit",
        "market": "Japan",
        "language": "en",
        "text": "We land at Haneda around midnight with two kids and four suitcases. Is airport pickup better than the last train?",
        "location": "Haneda Airport",
        "season": "Chinese New Year Travel",
        "event": "late-night arrival",
        "source_confidence": 0.9,
    },
    {
        "source_id": "MANUAL-INTENT-002",
        "source_type": "manual_import",
        "platform": "Reddit",
        "market": "Japan",
        "language": "en",
        "text": "Looking for a private car day trip from Tokyo to Mount Fuji for parents who cannot walk long distances.",
        "location": "Mount Fuji",
        "season": "Autumn Leaves Season",
        "event": "Fuji sightseeing",
        "source_confidence": 0.86,
    },
    {
        "source_id": "MANUAL-INTENT-003",
        "source_type": "manual_import",
        "platform": "X",
        "market": "Japan",
        "language": "en",
        "text": "Suzuka F1 exit looks impossible. Need a pickup plan from the venue to Nagoya after the race.",
        "location": "Suzuka Circuit",
        "season": "Exhibitions Concerts Sports Events",
        "event": "F1 / racing",
        "source_confidence": 0.82,
    },
    {
        "source_id": "MANUAL-INTENT-004",
        "source_type": "manual_import",
        "platform": "TikTok",
        "market": "Japan",
        "language": "en",
        "text": "Tokyo train memes are funny lol, not traveling, just watching videos.",
        "location": "Tokyo",
        "season": "none",
        "event": "none",
        "source_confidence": 0.42,
    },
]


class MobilityDemandIntentEngine:
    """Classify whether a signal contains real mobility demand."""

    def __init__(self, root: str | Path = "runtime/mobility_demand_intent") -> None:
        self.root = Path(root)
        self.report_path = self.root / "MOBILITY_DEMAND_INTENT_REPORT.json"
        self.intents_path = self.root / "mobility_intents.json"
        self.high_value_path = self.root / "high_value_mobility_intents.json"
        self.low_value_path = self.root / "low_value_signals.json"
        self.summary_path = self.root / "mobility_intent_summary.json"

    def build(self, inputs: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        source_items = inputs if inputs is not None else self._default_sources()
        location_heatmap = LocationDemandHeatmapEngine().state().get("locationHeatmap", [])
        seasonal_calendar = SeasonalDemandCalendarEngine().state().get("seasonalCalendar", [])
        intents = [
            self._classify(index, item, location_heatmap, seasonal_calendar)
            for index, item in enumerate(source_items, start=1)
        ]
        high_value = [
            item
            for item in intents
            if item["demand_intent"] != "no_real_mobility_intent"
            and item["intent_strength_score"] >= 68
            and item["conversion_potential_score"] >= 55
            and item["confidence_score"] >= 55
        ]
        low_value = [self._low_value_signal(item) for item in intents if item not in high_value]
        summary = self._summary(intents, high_value, low_value)
        report = {
            "report_id": "MOBILITY_DEMAND_INTENT_REPORT",
            "created_at": utc_now_iso(),
            "status": "mobility_intents_classified",
            "phase": "PREDICTIVE_DEMAND_INTELLIGENCE",
            "supportedIntentTypes": SUPPORTED_INTENTS,
            "supportedInputSources": SUPPORTED_INPUT_SOURCES,
            "mobilityIntents": intents,
            "highValueMobilityIntents": high_value,
            "lowValueSignals": low_value,
            "mobilityIntentSummary": summary,
            "safetyBoundary": "Mobility Demand Intent Engine classifies local intelligence only. It does not quote prices, contact customers, dispatch drivers, post, reply, DM, log in, or call platform write APIs.",
        }
        self.persist(report)
        return report

    def build_from_json(self, path: str | Path) -> dict[str, Any]:
        inputs = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(inputs, list):
            raise ValueError("JSON import must be a list of mobility signal records")
        return self.build(inputs)

    def build_from_csv(self, path: str | Path) -> dict[str, Any]:
        with Path(path).open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        return self.build([dict(row, source_type="local_csv") for row in rows])

    def state(self) -> dict[str, Any]:
        if self.report_path.exists():
            return json.loads(self.report_path.read_text(encoding="utf-8"))
        return self.build()

    def persist(self, report: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.intents_path.write_text(json.dumps(report["mobilityIntents"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.high_value_path.write_text(json.dumps(report["highValueMobilityIntents"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.low_value_path.write_text(json.dumps(report["lowValueSignals"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.summary_path.write_text(json.dumps(report["mobilityIntentSummary"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    def _default_sources(self) -> list[dict[str, Any]]:
        sources: list[dict[str, Any]] = []
        sources.extend(self._from_normalized_live_data())
        sources.extend(self._from_question_inbox())
        sources.extend(self._from_api_signals())
        sources.extend(self._from_google_trends_keywords())
        sources.extend(DEFAULT_MANUAL_INPUTS)
        seen = set()
        deduped = []
        for item in sources:
            key = (item.get("source_type"), item.get("source_id"), item.get("text"))
            if key in seen:
                continue
            seen.add(key)
            deduped.append(item)
        return deduped

    @staticmethod
    def _from_normalized_live_data() -> list[dict[str, Any]]:
        items = LiveDataNormalizationPipeline().state().get("normalizedLiveData", [])
        return [
            {
                "source_id": item.get("normalized_id", ""),
                "source_type": "normalized_live_data",
                "platform": item.get("platform", "unknown"),
                "market": item.get("market", "unknown"),
                "language": item.get("language", "unknown"),
                "text": " ".join(str(item.get(key, "")) for key in ("topic", "keyword", "normalized_text")),
                "location": MobilityDemandIntentEngine._extract_location(" ".join(str(item.get(key, "")) for key in ("topic", "keyword", "normalized_text"))),
                "season": "",
                "event": "",
                "source_confidence": item.get("source_confidence", 0.5),
                "trend_strength": item.get("trend_strength", 0),
            }
            for item in items
        ]

    @staticmethod
    def _from_question_inbox() -> list[dict[str, Any]]:
        path = Path("runtime/live_memory_import/question_inbox_memory.json")
        if not path.exists():
            return []
        items = json.loads(path.read_text(encoding="utf-8"))
        return [
            {
                "source_id": item.get("question_id", ""),
                "source_type": "question_inbox",
                "platform": item.get("platform", "unknown"),
                "market": item.get("market", "unknown"),
                "language": item.get("language", "unknown"),
                "text": item.get("question_text", ""),
                "location": MobilityDemandIntentEngine._extract_location(item.get("question_text", "")),
                "season": "",
                "event": "",
                "source_confidence": min(0.95, max(0.3, item.get("priority_score", 50) / 100)),
                "trend_strength": item.get("priority_score", 0),
            }
            for item in items
        ]

    @staticmethod
    def _from_api_signals() -> list[dict[str, Any]]:
        items = APISignalNormalization().state().get("normalizedSignals", [])
        return [
            {
                "source_id": item.get("signal_id", ""),
                "source_type": "scout_intelligence",
                "platform": item.get("platform", "unknown"),
                "market": item.get("market", "unknown"),
                "language": item.get("language", "unknown"),
                "text": " ".join(str(item.get(key, "")) for key in ("topic", "keyword", "normalized_text")),
                "location": MobilityDemandIntentEngine._extract_location(" ".join(str(item.get(key, "")) for key in ("topic", "keyword", "normalized_text"))),
                "season": "",
                "event": "",
                "source_confidence": 0.75 if item.get("engagement_potential") == "high" else 0.6,
                "trend_strength": item.get("trend_strength", 0),
            }
            for item in items
        ]

    @staticmethod
    def _from_google_trends_keywords() -> list[dict[str, Any]]:
        items = SeasonalDemandCalendarEngine().state().get("seasonalKeywords", [])
        return [
            {
                "source_id": item.get("keyword_id", ""),
                "source_type": "google_trends_keyword_signal",
                "platform": "Google Trends structure",
                "market": "/".join(item.get("target_markets", [])[:3]) or "Japan",
                "language": "en",
                "text": item.get("keyword", ""),
                "location": MobilityDemandIntentEngine._extract_location(item.get("keyword", "")),
                "season": item.get("season_name", ""),
                "event": item.get("season_name", ""),
                "source_confidence": 0.58,
                "trend_strength": 60,
            }
            for item in items[:12]
        ]

    @staticmethod
    def _classify(
        index: int,
        item: dict[str, Any],
        location_heatmap: list[dict[str, Any]],
        seasonal_calendar: list[dict[str, Any]],
    ) -> dict[str, Any]:
        text = str(item.get("text") or item.get("question_text") or item.get("keyword") or "").strip()
        lowered = text.lower()
        low_reason = MobilityDemandIntentEngine._low_value_reason(lowered)
        matched_rule = None if low_reason else MobilityDemandIntentEngine._matched_intent_rule(lowered)
        location = item.get("location") or MobilityDemandIntentEngine._extract_location(text) or "unknown"
        location_record = MobilityDemandIntentEngine._location_record(location, location_heatmap)
        season = item.get("season") or MobilityDemandIntentEngine._infer_season(location_record, seasonal_calendar)
        event = item.get("event") or MobilityDemandIntentEngine._infer_event(location_record)
        confidence = MobilityDemandIntentEngine._confidence_score(item, matched_rule, low_reason)
        if matched_rule is None:
            demand_intent = "no_real_mobility_intent"
            strength = 22 if low_reason else 40
            conversion = 12 if low_reason else 28
            urgency = 8 if low_reason else 24
            route = "ignore_noise_or_monitor_only"
        else:
            demand_intent = matched_rule["intent"]
            heat_bonus = min(12, int(location_record.get("demand_heat_score", 55)) // 10) if location_record else 4
            source_bonus = min(8, int(item.get("trend_strength", 0)) // 15)
            strength = min(100, matched_rule["base_strength"] + heat_bonus + source_bonus)
            conversion = min(100, matched_rule["base_conversion"] + heat_bonus)
            urgency = min(100, matched_rule["base_urgency"] + (8 if "urgent" in lowered or "tonight" in lowered or "midnight" in lowered else 0))
            route = matched_rule["route"]
        return {
            "intent_id": f"MOBILITY-INTENT-{index:04d}",
            "source_id": item.get("source_id", f"SOURCE-{index:04d}"),
            "source_type": item.get("source_type", "manual_import"),
            "platform": item.get("platform", "unknown"),
            "market": item.get("market", "unknown"),
            "language": item.get("language", "unknown"),
            "location": location,
            "season": season,
            "event": event,
            "demand_intent": demand_intent,
            "intent_strength_score": strength,
            "conversion_potential_score": conversion,
            "urgency_score": urgency,
            "confidence_score": confidence,
            "recommended_route": route,
            "source_text": text,
            "low_value_reason": low_reason,
            "classification_reason": MobilityDemandIntentEngine._classification_reason(demand_intent, location, season, low_reason),
            "human_review_required": True,
            "auto_quote_enabled": False,
            "auto_customer_contact_enabled": False,
            "auto_dispatch_enabled": False,
            "auto_post_enabled": False,
            "auto_reply_enabled": False,
            "classified_at": utc_now_iso(),
        }

    @staticmethod
    def _matched_intent_rule(lowered: str) -> dict[str, Any] | None:
        for rule in INTENT_RULES:
            if any(keyword in lowered for keyword in rule["keywords"]):
                return rule
        return None

    @staticmethod
    def _low_value_reason(lowered: str) -> str:
        for reason, hints in LOW_VALUE_REASONS.items():
            if any(hint in lowered for hint in hints):
                return reason
        return ""

    @staticmethod
    def _extract_location(text: str) -> str:
        lowered = text.lower()
        locations = [
            "Haneda Airport",
            "Narita Airport",
            "Kansai Airport",
            "Chubu Centrair Airport",
            "Suzuka Circuit",
            "Tokyo Big Sight",
            "Mount Fuji",
            "Shinjuku",
            "Shibuya",
            "Ueno",
            "Tokyo",
            "Osaka",
            "Kyoto",
            "Nagoya",
            "Sapporo",
            "Okinawa",
        ]
        for location in locations:
            if location.lower() in lowered:
                return location
        return "unknown"

    @staticmethod
    def _location_record(location: str, heatmap: list[dict[str, Any]]) -> dict[str, Any]:
        for item in heatmap:
            if item.get("location_name") == location:
                return item
        return {}

    @staticmethod
    def _infer_season(location_record: dict[str, Any], seasonal_calendar: list[dict[str, Any]]) -> str:
        seasons = location_record.get("related_seasons", [])
        if seasons:
            return seasons[0]
        return seasonal_calendar[0].get("season_name", "") if seasonal_calendar else ""

    @staticmethod
    def _infer_event(location_record: dict[str, Any]) -> str:
        events = location_record.get("related_events", [])
        return events[0] if events else ""

    @staticmethod
    def _confidence_score(item: dict[str, Any], matched_rule: dict[str, Any] | None, low_reason: str) -> int:
        raw = item.get("source_confidence", 0.55)
        try:
            confidence = float(raw)
        except (TypeError, ValueError):
            confidence = 0.55
        score = round(confidence * 100)
        if matched_rule:
            score += 8
        if low_reason:
            score -= 25
        return max(0, min(100, score))

    @staticmethod
    def _classification_reason(intent: str, location: str, season: str, low_reason: str) -> str:
        if intent == "no_real_mobility_intent":
            return f"Signal routed to no_real_mobility_intent because it matches low-value pattern: {low_reason or 'no direct mobility need'}."
        return f"Signal contains {intent} language, location={location}, season={season}; route to human-reviewed operating strategy before any action."

    @staticmethod
    def _low_value_signal(intent: dict[str, Any]) -> dict[str, Any]:
        return {
            "intent_id": intent["intent_id"],
            "source_id": intent["source_id"],
            "platform": intent["platform"],
            "market": intent["market"],
            "language": intent["language"],
            "location": intent["location"],
            "demand_intent": intent["demand_intent"],
            "intent_strength_score": intent["intent_strength_score"],
            "confidence_score": intent["confidence_score"],
            "low_value_reason": intent["low_value_reason"] or "below_high_value_threshold",
            "recommended_route": "ignore_noise_or_monitor_only",
            "source_text": intent["source_text"],
        }

    @staticmethod
    def _summary(
        intents: list[dict[str, Any]],
        high_value: list[dict[str, Any]],
        low_value: list[dict[str, Any]],
    ) -> dict[str, Any]:
        return {
            "intent_engine_ready": True,
            "intents_classified": len(intents),
            "high_value_intents": len(high_value),
            "low_value_signals": len(low_value),
            "intent_types_detected": sorted({item["demand_intent"] for item in intents}),
            "high_value_routes": sorted({item["recommended_route"] for item in high_value}),
            "low_value_reasons": sorted({item["low_value_reason"] for item in low_value}),
            "supported_input_sources": SUPPORTED_INPUT_SOURCES,
            "auto_quote_enabled": False,
            "auto_customer_contact_enabled": False,
            "auto_dispatch_enabled": False,
            "auto_post_enabled": False,
            "auto_reply_enabled": False,
            "write_operations_enabled": False,
        }


if __name__ == "__main__":
    result = MobilityDemandIntentEngine().build()
    print(json.dumps({"status": result["status"], "summary": result["mobilityIntentSummary"]}, indent=2))
