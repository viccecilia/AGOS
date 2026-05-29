"""Seasonal intelligence engine for global predictive demand analysis."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from services.intelligence_ranking_noise_filter import IntelligenceRankingNoiseFilter
from services.market_intelligence_matrix import MarketIntelligenceMatrix
from services.runtime_persistence import utc_now_iso
from services.seasonal_demand_calendar_engine import SeasonalDemandCalendarEngine
from services.seasonal_trend_import_trial import SeasonalTrendImportTrial


DEFAULT_CALENDAR_PATH = Path("runtime/seasonal_demand_calendar/seasonal_calendar.json")
DEFAULT_TREND_MATCHES_PATH = Path("runtime/seasonal_trend_import_trial/seasonal_trend_matches.json")
DEFAULT_TREND_HEATMAP_PATH = Path("runtime/seasonal_trend_import_trial/seasonal_market_heatmap.json")
DEFAULT_MARKET_MATRIX_PATH = Path("runtime/market_intelligence_matrix/market_intelligence_matrix.json")
DEFAULT_RANKED_INTELLIGENCE_PATH = Path("runtime/intelligence_ranking/ranked_intelligence.json")
DEFAULT_OUTPUT_DIR = Path("runtime/seasonal_intelligence")


class SeasonalIntelligenceEngine:
    """Combine calendar, trend samples, market matrix, and ranked intelligence by season."""

    def __init__(
        self,
        calendar_path: str | Path = DEFAULT_CALENDAR_PATH,
        trend_matches_path: str | Path = DEFAULT_TREND_MATCHES_PATH,
        trend_heatmap_path: str | Path = DEFAULT_TREND_HEATMAP_PATH,
        market_matrix_path: str | Path = DEFAULT_MARKET_MATRIX_PATH,
        ranked_intelligence_path: str | Path = DEFAULT_RANKED_INTELLIGENCE_PATH,
        output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    ) -> None:
        self.calendar_path = Path(calendar_path)
        self.trend_matches_path = Path(trend_matches_path)
        self.trend_heatmap_path = Path(trend_heatmap_path)
        self.market_matrix_path = Path(market_matrix_path)
        self.ranked_intelligence_path = Path(ranked_intelligence_path)
        self.output_dir = Path(output_dir)
        self.report_path = self.output_dir / "SEASONAL_INTELLIGENCE_REPORT.json"
        self.intelligence_path = self.output_dir / "seasonal_intelligence.json"
        self.heatmap_path = self.output_dir / "season_market_heatmap.json"
        self.ranking_path = self.output_dir / "seasonal_demand_ranking.json"
        self.summary_path = self.output_dir / "seasonal_intelligence_summary.json"

    def build(
        self,
        calendar: list[dict[str, Any]] | None = None,
        trend_matches: list[dict[str, Any]] | None = None,
        trend_heatmap: list[dict[str, Any]] | None = None,
        market_matrix: list[dict[str, Any]] | None = None,
        ranked_intelligence: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        seasons = calendar if calendar is not None else self._load_calendar()
        matches = trend_matches if trend_matches is not None else self._load_trend_matches()
        heatmap = trend_heatmap if trend_heatmap is not None else self._load_trend_heatmap()
        markets = market_matrix if market_matrix is not None else self._load_market_matrix()
        ranked = ranked_intelligence if ranked_intelligence is not None else self._load_ranked_intelligence()

        seasonal_intelligence = self._seasonal_intelligence(seasons, matches, heatmap, markets, ranked)
        season_market_heatmap = self._season_market_heatmap(seasonal_intelligence)
        demand_ranking = self._demand_ranking(seasonal_intelligence)
        summary = self._summary(seasonal_intelligence, season_market_heatmap, demand_ranking)
        report = {
            "report_id": "SEASONAL_INTELLIGENCE_REPORT",
            "round_id": "ROUND-GLOBAL-007",
            "created_at": utc_now_iso(),
            "status": "seasonal_intelligence_ready",
            "phase": "GLOBAL_PREDICTIVE_INTELLIGENCE",
            "seasonalIntelligence": seasonal_intelligence,
            "seasonMarketHeatmap": season_market_heatmap,
            "seasonalDemandRanking": demand_ranking,
            "seasonalIntelligenceSummary": summary,
            "safetyBoundary": "Seasonal Intelligence Engine combines local calendar, sample trend imports, market matrix, and ranked intelligence only. It does not treat sample trend data as real prediction, auto-post, auto-reply, contact users, dispatch drivers, or call platform write APIs.",
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
        self.intelligence_path.write_text(json.dumps(report["seasonalIntelligence"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.heatmap_path.write_text(json.dumps(report["seasonMarketHeatmap"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.ranking_path.write_text(json.dumps(report["seasonalDemandRanking"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.summary_path.write_text(json.dumps(report["seasonalIntelligenceSummary"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    def _load_calendar(self) -> list[dict[str, Any]]:
        if not self.calendar_path.exists():
            SeasonalDemandCalendarEngine().build()
        payload = json.loads(self.calendar_path.read_text(encoding="utf-8")) if self.calendar_path.exists() else []
        return payload if isinstance(payload, list) else []

    def _load_trend_matches(self) -> list[dict[str, Any]]:
        if not self.trend_matches_path.exists():
            SeasonalTrendImportTrial().run()
        payload = json.loads(self.trend_matches_path.read_text(encoding="utf-8")) if self.trend_matches_path.exists() else []
        return payload if isinstance(payload, list) else []

    def _load_trend_heatmap(self) -> list[dict[str, Any]]:
        if not self.trend_heatmap_path.exists():
            SeasonalTrendImportTrial().run()
        payload = json.loads(self.trend_heatmap_path.read_text(encoding="utf-8")) if self.trend_heatmap_path.exists() else []
        return payload if isinstance(payload, list) else []

    def _load_market_matrix(self) -> list[dict[str, Any]]:
        if not self.market_matrix_path.exists():
            MarketIntelligenceMatrix().build()
        payload = json.loads(self.market_matrix_path.read_text(encoding="utf-8")) if self.market_matrix_path.exists() else []
        return payload if isinstance(payload, list) else []

    def _load_ranked_intelligence(self) -> list[dict[str, Any]]:
        if not self.ranked_intelligence_path.exists():
            IntelligenceRankingNoiseFilter().build()
        payload = json.loads(self.ranked_intelligence_path.read_text(encoding="utf-8")) if self.ranked_intelligence_path.exists() else []
        return payload if isinstance(payload, list) else []

    @classmethod
    def _seasonal_intelligence(
        cls,
        seasons: list[dict[str, Any]],
        trend_matches: list[dict[str, Any]],
        trend_heatmap: list[dict[str, Any]],
        market_matrix: list[dict[str, Any]],
        ranked_intelligence: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        market_by_name = {item.get("market"): item for item in market_matrix}
        heat_by_key = {
            (item.get("season_id"), item.get("target_market")): item
            for item in trend_heatmap
            if item.get("season_id") != "NO_MATCH"
        }
        matches_by_key: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        for item in trend_matches:
            if item.get("matched_season_id") != "NO_MATCH":
                matches_by_key[(item.get("matched_season_id", ""), item.get("target_market", ""))].append(item)

        rows: list[dict[str, Any]] = []
        for season in seasons:
            markets = cls._target_markets(season, market_by_name)
            for market_name in markets[:4]:
                market = market_by_name.get(market_name, {})
                heat = heat_by_key.get((season.get("season_id"), market_name), {})
                matches = matches_by_key.get((season.get("season_id", ""), market_name), [])
                related_ranked = cls._related_ranked_intelligence(season, market_name, ranked_intelligence)
                pain_clusters = cls._pain_clusters(season, related_ranked)
                heat_score = cls._heat_score(season, market, heat, matches, related_ranked)
                confidence = cls._confidence_score(heat, matches, related_ranked)
                rows.append(
                    {
                        "season_id": season.get("season_id", ""),
                        "season_name": season.get("season_name", ""),
                        "market": market_name,
                        "time_window": season.get("time_window", ""),
                        "likely_locations": season.get("likely_locations", []),
                        "demand_keywords": season.get("demand_keywords", []),
                        "pain_clusters": pain_clusters,
                        "mobility_demand_types": season.get("predicted_demand_types", []),
                        "seasonal_heat_score": heat_score,
                        "confidence_score": confidence,
                        "human_review_required": True,
                        "sample_data_only": True,
                        "confirmed_prediction": False,
                        "source_status": cls._source_status(matches, heat),
                        "related_ranked_intelligence_ids": [item.get("intelligence_id", "") for item in related_ranked[:5]],
                        "trend_match_count": len(matches),
                        "market_opportunity_score": market.get("opportunity_score", 0),
                        "auto_publish_allowed": False,
                        "auto_reply_allowed": False,
                        "write_api_allowed": False,
                    }
                )
        return sorted(rows, key=lambda item: item["seasonal_heat_score"], reverse=True)

    @staticmethod
    def _target_markets(season: dict[str, Any], market_by_name: dict[str, dict[str, Any]]) -> list[str]:
        aliases = {"China": "China outbound", "Hong Kong": "China outbound", "Japan domestic": "Japan"}
        mapped = [aliases.get(item, item) for item in season.get("target_markets", [])]
        markets = [item for item in mapped if item in market_by_name]
        if markets:
            return list(dict.fromkeys(markets))
        return list(market_by_name)[:3] or ["needs_review"]

    @staticmethod
    def _related_ranked_intelligence(
        season: dict[str, Any],
        market: str,
        ranked_intelligence: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        season_text = " ".join(
            [
                season.get("season_name", ""),
                " ".join(season.get("likely_locations", [])),
                " ".join(season.get("demand_keywords", [])),
                " ".join(season.get("mobility_pain_points", [])),
                " ".join(season.get("predicted_demand_types", [])),
            ]
        ).lower()
        related = []
        for item in ranked_intelligence:
            if item.get("ranking_status") not in {"high_value", "monitor"}:
                continue
            item_text = " ".join(
                [
                    item.get("market", ""),
                    item.get("platform", ""),
                    item.get("pain_cluster", ""),
                    item.get("source_pain", ""),
                    item.get("evidence_summary", {}).get("content_expansion_fit", ""),
                ]
            ).lower()
            market_match = item.get("market") == market
            keyword_match = any(token and token in item_text for token in season_text.split() if len(token) >= 6)
            if market_match or keyword_match:
                related.append(item)
        return sorted(related, key=lambda item: item.get("total_score", 0), reverse=True)

    @staticmethod
    def _pain_clusters(season: dict[str, Any], ranked: list[dict[str, Any]]) -> list[str]:
        values = [item.get("pain_cluster", "") for item in ranked if item.get("pain_cluster")]
        values.extend(season.get("mobility_pain_points", [])[:3])
        return list(dict.fromkeys(values))[:6]

    @staticmethod
    def _heat_score(
        season: dict[str, Any],
        market: dict[str, Any],
        heat: dict[str, Any],
        matches: list[dict[str, Any]],
        related_ranked: list[dict[str, Any]],
    ) -> int:
        calendar_base = 52 + min(18, len(season.get("demand_keywords", [])) * 3)
        trend_heat = int(float(heat.get("heat_score", 0))) if heat else 0
        market_score = int(market.get("opportunity_score", 0))
        ranked_score = round(sum(item.get("total_score", 0) for item in related_ranked[:3]) / max(1, min(3, len(related_ranked))))
        match_bonus = min(12, len(matches) * 3)
        score = round(calendar_base * 0.25 + trend_heat * 0.25 + market_score * 0.25 + ranked_score * 0.2 + match_bonus)
        return max(0, min(100, score))

    @staticmethod
    def _confidence_score(
        heat: dict[str, Any],
        matches: list[dict[str, Any]],
        related_ranked: list[dict[str, Any]],
    ) -> int:
        heat_confidence = int(float(heat.get("average_confidence", 0))) if heat else 0
        match_confidence = round(sum(item.get("confidence_score", 0) for item in matches) / max(1, len(matches))) if matches else 0
        evidence_confidence = round(sum(item.get("score_breakdown", {}).get("evidence_confidence", 0) for item in related_ranked[:3]) / max(1, min(3, len(related_ranked)))) if related_ranked else 0
        score = round(heat_confidence * 0.35 + match_confidence * 0.3 + evidence_confidence * 0.25 + min(10, len(matches) * 2))
        return max(18, min(88, score))

    @staticmethod
    def _source_status(matches: list[dict[str, Any]], heat: dict[str, Any]) -> str:
        if matches or heat:
            return "sample_trend_plus_calendar_plus_ranked_intelligence"
        return "calendar_plus_market_matrix_only"

    @staticmethod
    def _season_market_heatmap(seasonal_intelligence: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "season_id": item["season_id"],
                "season_name": item["season_name"],
                "market": item["market"],
                "heat_score": item["seasonal_heat_score"],
                "confidence_score": item["confidence_score"],
                "sample_data_only": item["sample_data_only"],
                "human_review_required": item["human_review_required"],
            }
            for item in seasonal_intelligence
        ]

    @staticmethod
    def _demand_ranking(seasonal_intelligence: list[dict[str, Any]]) -> list[dict[str, Any]]:
        counter: Counter[str] = Counter()
        heat_sum: Counter[str] = Counter()
        for item in seasonal_intelligence:
            for demand_type in item.get("mobility_demand_types", []):
                counter[demand_type] += 1
                heat_sum[demand_type] += item.get("seasonal_heat_score", 0)
        rows = []
        for demand_type, count in counter.most_common():
            rows.append(
                {
                    "demand_type": demand_type,
                    "season_market_count": count,
                    "average_heat_score": round(heat_sum[demand_type] / max(1, count), 2),
                    "sample_data_only": True,
                    "human_review_required": True,
                    "auto_action_allowed": False,
                }
            )
        return rows

    @staticmethod
    def _summary(
        seasonal_intelligence: list[dict[str, Any]],
        season_market_heatmap: list[dict[str, Any]],
        demand_ranking: list[dict[str, Any]],
    ) -> dict[str, Any]:
        seasons = sorted({item["season_id"] for item in seasonal_intelligence})
        markets = sorted({item["market"] for item in seasonal_intelligence})
        top_rows = sorted(seasonal_intelligence, key=lambda item: item["seasonal_heat_score"], reverse=True)[:5]
        return {
            "seasonal_intelligence_ready": True,
            "season_count": len(seasons),
            "season_market_rows": len(seasonal_intelligence),
            "market_count": len(markets),
            "heatmap_rows": len(season_market_heatmap),
            "demand_type_count": len(demand_ranking),
            "top_season_markets": [
                {
                    "season_name": item["season_name"],
                    "market": item["market"],
                    "heat_score": item["seasonal_heat_score"],
                    "confidence_score": item["confidence_score"],
                }
                for item in top_rows
            ],
            "sample_data_only": True,
            "confirmed_prediction": False,
            "real_external_api_connected": False,
            "all_items_human_review_required": all(item["human_review_required"] for item in seasonal_intelligence),
            "auto_publish_allowed": False,
            "auto_reply_allowed": False,
            "write_api_allowed": False,
            "next_recommendation": "Use reviewed seasonal intelligence as input for Spatial Intelligence Engine; do not treat sample trend heat as confirmed demand.",
        }
