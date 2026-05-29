"""Spatial intelligence engine for global predictive demand analysis."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from services.intelligence_ranking_noise_filter import IntelligenceRankingNoiseFilter
from services.location_demand_heatmap_engine import LocationDemandHeatmapEngine
from services.market_intelligence_matrix import MarketIntelligenceMatrix
from services.runtime_persistence import utc_now_iso
from services.seasonal_intelligence_engine import SeasonalIntelligenceEngine


DEFAULT_LOCATION_HEATMAP_PATH = Path("runtime/location_demand_heatmap/location_heatmap.json")
DEFAULT_MARKET_MATRIX_PATH = Path("runtime/market_intelligence_matrix/market_intelligence_matrix.json")
DEFAULT_SEASONAL_INTELLIGENCE_PATH = Path("runtime/seasonal_intelligence/seasonal_intelligence.json")
DEFAULT_RANKED_INTELLIGENCE_PATH = Path("runtime/intelligence_ranking/ranked_intelligence.json")
DEFAULT_OUTPUT_DIR = Path("runtime/spatial_intelligence")

SUPPORTED_SPATIAL_TYPES = [
    "country",
    "city",
    "airport",
    "station",
    "attraction",
    "hotel_zone",
    "event_venue",
    "business_district",
    "shopping_district",
]

LOCATION_TYPE_MAP = {
    "city": "city",
    "airport": "airport",
    "attraction": "attraction",
    "racing_venue": "event_venue",
    "exhibition_center": "event_venue",
    "commercial_district": "shopping_district",
}


class SpatialIntelligenceEngine:
    """Combine location, market, seasonal, and ranked intelligence by place."""

    def __init__(
        self,
        location_heatmap_path: str | Path = DEFAULT_LOCATION_HEATMAP_PATH,
        market_matrix_path: str | Path = DEFAULT_MARKET_MATRIX_PATH,
        seasonal_intelligence_path: str | Path = DEFAULT_SEASONAL_INTELLIGENCE_PATH,
        ranked_intelligence_path: str | Path = DEFAULT_RANKED_INTELLIGENCE_PATH,
        output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    ) -> None:
        self.location_heatmap_path = Path(location_heatmap_path)
        self.market_matrix_path = Path(market_matrix_path)
        self.seasonal_intelligence_path = Path(seasonal_intelligence_path)
        self.ranked_intelligence_path = Path(ranked_intelligence_path)
        self.output_dir = Path(output_dir)
        self.report_path = self.output_dir / "SPATIAL_INTELLIGENCE_REPORT.json"
        self.spatial_path = self.output_dir / "spatial_intelligence.json"
        self.heatmap_path = self.output_dir / "location_market_heatmap.json"
        self.ranking_path = self.output_dir / "spatial_demand_ranking.json"
        self.summary_path = self.output_dir / "spatial_intelligence_summary.json"

    def build(
        self,
        location_heatmap: list[dict[str, Any]] | None = None,
        market_matrix: list[dict[str, Any]] | None = None,
        seasonal_intelligence: list[dict[str, Any]] | None = None,
        ranked_intelligence: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        locations = location_heatmap if location_heatmap is not None else self._load_location_heatmap()
        markets = market_matrix if market_matrix is not None else self._load_market_matrix()
        seasonal = seasonal_intelligence if seasonal_intelligence is not None else self._load_seasonal_intelligence()
        ranked = ranked_intelligence if ranked_intelligence is not None else self._load_ranked_intelligence()

        spatial = self._spatial_intelligence(locations, markets, seasonal, ranked)
        location_market_heatmap = self._location_market_heatmap(spatial)
        demand_ranking = self._demand_ranking(spatial)
        summary = self._summary(spatial, location_market_heatmap, demand_ranking)
        report = {
            "report_id": "SPATIAL_INTELLIGENCE_REPORT",
            "round_id": "ROUND-GLOBAL-008",
            "created_at": utc_now_iso(),
            "status": "spatial_intelligence_ready",
            "phase": "GLOBAL_PREDICTIVE_INTELLIGENCE",
            "supportedSpatialTypes": SUPPORTED_SPATIAL_TYPES,
            "spatialIntelligence": spatial,
            "locationMarketHeatmap": location_market_heatmap,
            "spatialDemandRanking": demand_ranking,
            "spatialIntelligenceSummary": summary,
            "safetyBoundary": "Spatial Intelligence Engine builds location demand intelligence from local/sample/read-only inputs only. It does not enable real-time GPS dispatch, contact drivers, quote prices, publish content, reply to users, or call platform write APIs.",
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
        self.spatial_path.write_text(json.dumps(report["spatialIntelligence"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.heatmap_path.write_text(json.dumps(report["locationMarketHeatmap"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.ranking_path.write_text(json.dumps(report["spatialDemandRanking"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.summary_path.write_text(json.dumps(report["spatialIntelligenceSummary"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    def _load_location_heatmap(self) -> list[dict[str, Any]]:
        if not self.location_heatmap_path.exists():
            LocationDemandHeatmapEngine().build()
        payload = json.loads(self.location_heatmap_path.read_text(encoding="utf-8")) if self.location_heatmap_path.exists() else []
        return payload if isinstance(payload, list) else []

    def _load_market_matrix(self) -> list[dict[str, Any]]:
        if not self.market_matrix_path.exists():
            MarketIntelligenceMatrix().build()
        payload = json.loads(self.market_matrix_path.read_text(encoding="utf-8")) if self.market_matrix_path.exists() else []
        return payload if isinstance(payload, list) else []

    def _load_seasonal_intelligence(self) -> list[dict[str, Any]]:
        if not self.seasonal_intelligence_path.exists():
            SeasonalIntelligenceEngine().build()
        payload = json.loads(self.seasonal_intelligence_path.read_text(encoding="utf-8")) if self.seasonal_intelligence_path.exists() else []
        return payload if isinstance(payload, list) else []

    def _load_ranked_intelligence(self) -> list[dict[str, Any]]:
        if not self.ranked_intelligence_path.exists():
            IntelligenceRankingNoiseFilter().build()
        payload = json.loads(self.ranked_intelligence_path.read_text(encoding="utf-8")) if self.ranked_intelligence_path.exists() else []
        return payload if isinstance(payload, list) else []

    @classmethod
    def _spatial_intelligence(
        cls,
        locations: list[dict[str, Any]],
        markets: list[dict[str, Any]],
        seasonal: list[dict[str, Any]],
        ranked: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        market_by_name = {item.get("market"): item for item in markets}
        seasonal_by_location = cls._seasonal_by_location(locations, seasonal)
        rows: list[dict[str, Any]] = []
        for location in locations:
            related_seasonal = seasonal_by_location.get(location.get("location_name"), [])
            candidate_markets = cls._candidate_markets(location, related_seasonal, markets)
            for market_name in candidate_markets[:3]:
                market = market_by_name.get(market_name, {})
                seasonal_rows = [item for item in related_seasonal if item.get("market") == market_name]
                related_ranked = cls._related_ranked(location, market_name, ranked)
                demand_heat = cls._demand_heat_score(location, market, seasonal_rows, related_ranked)
                confidence = cls._confidence_score(location, seasonal_rows, related_ranked)
                rows.append(
                    {
                        "location_id": location.get("location_id", ""),
                        "location_name": location.get("location_name", ""),
                        "location_type": cls._normalize_location_type(location.get("location_type", "")),
                        "raw_location_type": location.get("location_type", ""),
                        "country": "Japan",
                        "region": location.get("region", ""),
                        "market": market_name,
                        "related_seasons": cls._related_seasons(location, seasonal_rows),
                        "related_events": location.get("related_events", []),
                        "pain_clusters": cls._pain_clusters(location, related_ranked),
                        "mobility_need": cls._mobility_need(location, market),
                        "mobility_demand_types": location.get("mobility_demand_types", []),
                        "crowd_pressure_score": int(location.get("crowd_risk_score", 0)),
                        "transfer_complexity_score": int(location.get("transfer_complexity_score", 0)),
                        "luggage_difficulty_score": int(location.get("luggage_difficulty_score", 0)),
                        "demand_heat_score": demand_heat,
                        "confidence_score": confidence,
                        "market_opportunity_score": int(market.get("opportunity_score", 0)),
                        "seasonal_signal_count": len(seasonal_rows),
                        "related_ranked_intelligence_ids": [item.get("intelligence_id", "") for item in related_ranked[:5]],
                        "human_review_required": True,
                        "sample_data_only": True,
                        "gps_dispatch_enabled": False,
                        "automatic_driver_contact_enabled": False,
                        "auto_publish_allowed": False,
                        "auto_reply_allowed": False,
                        "write_api_allowed": False,
                    }
                )
        return sorted(rows, key=lambda item: item["demand_heat_score"], reverse=True)

    @staticmethod
    def _seasonal_by_location(
        locations: list[dict[str, Any]],
        seasonal: list[dict[str, Any]],
    ) -> dict[str, list[dict[str, Any]]]:
        aliases = {
            "Haneda Airport": {"Haneda Airport", "Tokyo"},
            "Narita Airport": {"Narita Airport", "Tokyo"},
            "Kansai Airport": {"Kansai Airport", "Osaka"},
            "Chubu Centrair Airport": {"Chubu Centrair Airport", "Nagoya"},
            "Suzuka Circuit": {"Suzuka Circuit", "Nagoya"},
            "Tokyo Big Sight": {"Tokyo Big Sight", "Tokyo"},
            "Mount Fuji": {"Mount Fuji", "Tokyo"},
        }
        result: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for location in locations:
            names = aliases.get(location.get("location_name", ""), {location.get("location_name", "")})
            for item in seasonal:
                if names & set(item.get("likely_locations", [])):
                    result[location.get("location_name", "")].append(item)
        return result

    @staticmethod
    def _candidate_markets(
        location: dict[str, Any],
        seasonal_rows: list[dict[str, Any]],
        markets: list[dict[str, Any]],
    ) -> list[str]:
        values = [item.get("market", "") for item in seasonal_rows if item.get("market")]
        if not values:
            values = [item.get("market", "") for item in sorted(markets, key=lambda row: row.get("opportunity_score", 0), reverse=True)]
        if location.get("location_type") == "airport" and "China outbound" in [item.get("market") for item in markets]:
            values.insert(0, "China outbound")
        return list(dict.fromkeys([item for item in values if item])) or ["needs_review"]

    @staticmethod
    def _normalize_location_type(value: str) -> str:
        return LOCATION_TYPE_MAP.get(value, value or "needs_review")

    @staticmethod
    def _related_ranked(location: dict[str, Any], market: str, ranked: list[dict[str, Any]]) -> list[dict[str, Any]]:
        location_text = " ".join(
            [
                location.get("location_name", ""),
                location.get("region", ""),
                " ".join(location.get("mobility_demand_types", [])),
                " ".join(location.get("common_pain_points", [])),
            ]
        ).lower()
        rows = []
        for item in ranked:
            if item.get("ranking_status") not in {"high_value", "monitor"}:
                continue
            item_text = " ".join(
                [
                    item.get("market", ""),
                    item.get("pain_cluster", ""),
                    item.get("source_pain", ""),
                    item.get("evidence_summary", {}).get("content_expansion_fit", ""),
                ]
            ).lower()
            if item.get("market") == market or any(token in item_text for token in location_text.split() if len(token) >= 6):
                rows.append(item)
        return sorted(rows, key=lambda item: item.get("total_score", 0), reverse=True)

    @staticmethod
    def _related_seasons(location: dict[str, Any], seasonal_rows: list[dict[str, Any]]) -> list[str]:
        values = [item.get("season_name", "") for item in seasonal_rows if item.get("season_name")]
        values.extend(location.get("related_seasons", []))
        return list(dict.fromkeys(values))[:8]

    @staticmethod
    def _pain_clusters(location: dict[str, Any], ranked: list[dict[str, Any]]) -> list[str]:
        values = [item.get("pain_cluster", "") for item in ranked if item.get("pain_cluster")]
        values.extend(location.get("common_pain_points", []))
        return list(dict.fromkeys(values))[:6]

    @staticmethod
    def _mobility_need(location: dict[str, Any], market: dict[str, Any]) -> str:
        market_need = market.get("mobility_need", "")
        location_need = ", ".join(location.get("mobility_demand_types", [])[:4])
        return f"{location_need}; market need: {market_need}" if market_need else location_need

    @staticmethod
    def _demand_heat_score(
        location: dict[str, Any],
        market: dict[str, Any],
        seasonal_rows: list[dict[str, Any]],
        related_ranked: list[dict[str, Any]],
    ) -> int:
        location_heat = int(location.get("demand_heat_score", 0))
        market_score = int(market.get("opportunity_score", 0))
        seasonal_score = round(sum(item.get("seasonal_heat_score", 0) for item in seasonal_rows[:3]) / max(1, min(3, len(seasonal_rows)))) if seasonal_rows else 0
        ranked_score = round(sum(item.get("total_score", 0) for item in related_ranked[:3]) / max(1, min(3, len(related_ranked)))) if related_ranked else 0
        event_bonus = 6 if location.get("related_events") else 0
        score = round(location_heat * 0.34 + market_score * 0.22 + seasonal_score * 0.26 + ranked_score * 0.14 + event_bonus)
        return max(0, min(100, score))

    @staticmethod
    def _confidence_score(
        location: dict[str, Any],
        seasonal_rows: list[dict[str, Any]],
        related_ranked: list[dict[str, Any]],
    ) -> int:
        location_confidence = 66 if location.get("data_origin") == "local_sample" else 50
        seasonal_confidence = round(sum(item.get("confidence_score", 0) for item in seasonal_rows[:3]) / max(1, min(3, len(seasonal_rows)))) if seasonal_rows else 0
        ranked_confidence = round(sum(item.get("score_breakdown", {}).get("evidence_confidence", 0) for item in related_ranked[:3]) / max(1, min(3, len(related_ranked)))) if related_ranked else 0
        score = round(location_confidence * 0.32 + seasonal_confidence * 0.36 + ranked_confidence * 0.22 + min(10, len(seasonal_rows) * 2))
        return max(20, min(88, score))

    @staticmethod
    def _location_market_heatmap(spatial: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "location_id": item["location_id"],
                "location_name": item["location_name"],
                "location_type": item["location_type"],
                "market": item["market"],
                "demand_heat_score": item["demand_heat_score"],
                "confidence_score": item["confidence_score"],
                "human_review_required": item["human_review_required"],
                "gps_dispatch_enabled": item["gps_dispatch_enabled"],
            }
            for item in spatial
        ]

    @staticmethod
    def _demand_ranking(spatial: list[dict[str, Any]]) -> list[dict[str, Any]]:
        heat: Counter[str] = Counter()
        count: Counter[str] = Counter()
        for item in spatial:
            for demand_type in item.get("mobility_demand_types", []):
                heat[demand_type] += item.get("demand_heat_score", 0)
                count[demand_type] += 1
        return [
            {
                "demand_type": demand_type,
                "location_market_count": count[demand_type],
                "average_heat_score": round(heat[demand_type] / max(1, count[demand_type]), 2),
                "human_review_required": True,
                "gps_dispatch_enabled": False,
                "automatic_driver_contact_enabled": False,
            }
            for demand_type, _ in heat.most_common()
        ]

    @staticmethod
    def _summary(
        spatial: list[dict[str, Any]],
        heatmap: list[dict[str, Any]],
        demand_ranking: list[dict[str, Any]],
    ) -> dict[str, Any]:
        location_names = sorted({item["location_name"] for item in spatial})
        types = sorted({item["location_type"] for item in spatial})
        markets = sorted({item["market"] for item in spatial})
        top_locations = sorted(spatial, key=lambda item: item["demand_heat_score"], reverse=True)[:8]
        return {
            "spatial_intelligence_ready": True,
            "location_count": len(location_names),
            "location_market_rows": len(spatial),
            "market_count": len(markets),
            "location_types": types,
            "heatmap_rows": len(heatmap),
            "demand_type_count": len(demand_ranking),
            "top_location_markets": [
                {
                    "location_name": item["location_name"],
                    "location_type": item["location_type"],
                    "market": item["market"],
                    "demand_heat_score": item["demand_heat_score"],
                    "confidence_score": item["confidence_score"],
                }
                for item in top_locations
            ],
            "sample_data_only": True,
            "real_time_gps_connected": False,
            "gps_dispatch_enabled": False,
            "automatic_driver_contact_enabled": False,
            "automatic_vehicle_contact_enabled": False,
            "all_items_human_review_required": all(item["human_review_required"] for item in spatial),
            "auto_publish_allowed": False,
            "auto_reply_allowed": False,
            "write_api_allowed": False,
            "next_recommendation": "Use reviewed spatial intelligence as input for Event Intelligence Engine; do not dispatch vehicles or contact drivers automatically.",
        }
