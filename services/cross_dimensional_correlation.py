"""Cross-dimensional correlation for global predictive intelligence."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from services.demand_prediction_engine import DemandPredictionEngine
from services.event_intelligence_engine import EventIntelligenceEngine
from services.market_intelligence_matrix import MarketIntelligenceMatrix
from services.mobility_intelligence_engine import MobilityIntelligenceEngine
from services.platform_pain_intelligence import PlatformPainIntelligence
from services.runtime_persistence import utc_now_iso
from services.seasonal_intelligence_engine import SeasonalIntelligenceEngine
from services.spatial_intelligence_engine import SpatialIntelligenceEngine


DEFAULT_SEASONAL_INTELLIGENCE_PATH = Path("runtime/seasonal_intelligence/seasonal_intelligence.json")
DEFAULT_SPATIAL_INTELLIGENCE_PATH = Path("runtime/spatial_intelligence/spatial_intelligence.json")
DEFAULT_EVENT_INTELLIGENCE_PATH = Path("runtime/event_intelligence/event_intelligence.json")
DEFAULT_MOBILITY_INTELLIGENCE_PATH = Path("runtime/mobility_intelligence/mobility_intelligence.json")
DEFAULT_DEMAND_PREDICTION_PATH = Path("runtime/demand_prediction/demand_predictions.json")
DEFAULT_PLATFORM_PAIN_PATH = Path("runtime/platform_pain_intelligence/platform_pain_profiles.json")
DEFAULT_MARKET_MATRIX_PATH = Path("runtime/market_intelligence_matrix/market_intelligence_matrix.json")
DEFAULT_OUTPUT_DIR = Path("runtime/cross_dimensional_correlation")


class CrossDimensionalCorrelation:
    """Connect time, space, event, platform, market, pain, and mobility signals."""

    def __init__(
        self,
        seasonal_intelligence_path: str | Path = DEFAULT_SEASONAL_INTELLIGENCE_PATH,
        spatial_intelligence_path: str | Path = DEFAULT_SPATIAL_INTELLIGENCE_PATH,
        event_intelligence_path: str | Path = DEFAULT_EVENT_INTELLIGENCE_PATH,
        mobility_intelligence_path: str | Path = DEFAULT_MOBILITY_INTELLIGENCE_PATH,
        demand_prediction_path: str | Path = DEFAULT_DEMAND_PREDICTION_PATH,
        platform_pain_path: str | Path = DEFAULT_PLATFORM_PAIN_PATH,
        market_matrix_path: str | Path = DEFAULT_MARKET_MATRIX_PATH,
        output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    ) -> None:
        self.seasonal_intelligence_path = Path(seasonal_intelligence_path)
        self.spatial_intelligence_path = Path(spatial_intelligence_path)
        self.event_intelligence_path = Path(event_intelligence_path)
        self.mobility_intelligence_path = Path(mobility_intelligence_path)
        self.demand_prediction_path = Path(demand_prediction_path)
        self.platform_pain_path = Path(platform_pain_path)
        self.market_matrix_path = Path(market_matrix_path)
        self.output_dir = Path(output_dir)
        self.report_path = self.output_dir / "CROSS_DIMENSIONAL_CORRELATION_REPORT.json"
        self.chains_path = self.output_dir / "correlation_chains.json"
        self.heatmap_path = self.output_dir / "cross_dimension_heatmap.json"
        self.strategy_path = self.output_dir / "strategy_signal_candidates.json"
        self.summary_path = self.output_dir / "cross_dimensional_correlation_summary.json"

    def build(
        self,
        seasonal_intelligence: list[dict[str, Any]] | None = None,
        spatial_intelligence: list[dict[str, Any]] | None = None,
        event_intelligence: list[dict[str, Any]] | None = None,
        mobility_intelligence: list[dict[str, Any]] | None = None,
        demand_predictions: list[dict[str, Any]] | None = None,
        platform_pain_profiles: list[dict[str, Any]] | None = None,
        market_matrix: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        seasonal = seasonal_intelligence if seasonal_intelligence is not None else self._load_seasonal_intelligence()
        spatial = spatial_intelligence if spatial_intelligence is not None else self._load_spatial_intelligence()
        events = event_intelligence if event_intelligence is not None else self._load_event_intelligence()
        mobility = mobility_intelligence if mobility_intelligence is not None else self._load_mobility_intelligence()
        predictions = demand_predictions if demand_predictions is not None else self._load_demand_predictions()
        platforms = platform_pain_profiles if platform_pain_profiles is not None else self._load_platform_pain_profiles()
        markets = market_matrix if market_matrix is not None else self._load_market_matrix()

        chains = self._chains(seasonal, spatial, events, mobility, predictions, platforms, markets)
        heatmap = self._heatmap(chains)
        strategy_candidates = self._strategy_candidates(chains)
        summary = self._summary(chains, heatmap, strategy_candidates)
        report = {
            "report_id": "CROSS_DIMENSIONAL_CORRELATION_REPORT",
            "round_id": "ROUND-GLOBAL-012",
            "created_at": utc_now_iso(),
            "status": "cross_dimensional_correlation_ready",
            "phase": "GLOBAL_PREDICTIVE_INTELLIGENCE",
            "correlationDimensions": [
                "season",
                "location",
                "event",
                "platform",
                "market",
                "pain",
                "mobility demand",
            ],
            "correlationChains": chains,
            "crossDimensionHeatmap": heatmap,
            "strategySignalCandidates": strategy_candidates,
            "crossDimensionalCorrelationSummary": summary,
            "safetyBoundary": "Cross-Dimensional Correlation creates explainable, human-reviewed strategy signals from local/sample/read-only intelligence. It does not publish, reply, contact customers, quote, dispatch vehicles, log in, scrape restricted data, or call platform write APIs.",
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
        self.chains_path.write_text(json.dumps(report["correlationChains"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.heatmap_path.write_text(json.dumps(report["crossDimensionHeatmap"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.strategy_path.write_text(json.dumps(report["strategySignalCandidates"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.summary_path.write_text(json.dumps(report["crossDimensionalCorrelationSummary"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

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

    def _load_demand_predictions(self) -> list[dict[str, Any]]:
        if not self.demand_prediction_path.exists():
            DemandPredictionEngine().build()
        return self._load_list(self.demand_prediction_path)

    def _load_platform_pain_profiles(self) -> list[dict[str, Any]]:
        if not self.platform_pain_path.exists():
            PlatformPainIntelligence().build()
        return self._load_list(self.platform_pain_path)

    def _load_market_matrix(self) -> list[dict[str, Any]]:
        if not self.market_matrix_path.exists():
            MarketIntelligenceMatrix().build()
        return self._load_list(self.market_matrix_path)

    @staticmethod
    def _load_list(path: Path) -> list[dict[str, Any]]:
        payload = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
        return payload if isinstance(payload, list) else []

    @classmethod
    def _chains(
        cls,
        seasonal: list[dict[str, Any]],
        spatial: list[dict[str, Any]],
        events: list[dict[str, Any]],
        mobility: list[dict[str, Any]],
        predictions: list[dict[str, Any]],
        platforms: list[dict[str, Any]],
        markets: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        spatial_index = cls._spatial_index(spatial)
        event_index = cls._event_index(events)
        mobility_index = cls._mobility_index(mobility)
        market_index = {item.get("market"): item for item in markets}
        platform_index = {item.get("platform"): item for item in platforms}
        candidates = [
            item
            for item in predictions
            if not item.get("low_confidence") and item.get("demand_type") != "no real mobility intent"
        ]
        candidates.extend([item for item in predictions if item not in candidates][:8])
        chains: list[dict[str, Any]] = []
        seen: set[tuple[str, str, str, str]] = set()
        for prediction in candidates:
            market = prediction.get("market", "needs_review")
            location = prediction.get("location", "needs_review")
            demand_type = prediction.get("demand_type", "needs_review")
            event_name = prediction.get("event", "none")
            mobility_match = cls._match_mobility(prediction, mobility_index)
            seasonal_match = cls._match_season(prediction, seasonal, mobility_match)
            spatial_match = spatial_index.get((market, location), spatial_index.get(("*", location), {}))
            event_match = event_index.get((market, event_name), event_index.get(("*", event_name), {}))
            market_match = market_index.get(market, {})
            platform = cls._platform(market_match, platform_index, demand_type)
            platform_match = platform_index.get(platform, {})
            pain_cluster = cls._pain_cluster(seasonal_match, spatial_match, platform_match, market_match, prediction)
            key = (market, location, event_name, demand_type)
            if key in seen:
                continue
            seen.add(key)
            confidence = cls._confidence(prediction, seasonal_match, spatial_match, event_match, mobility_match, market_match, platform_match)
            strategy_type = cls._strategy_type(demand_type, event_name, location, platform)
            evidence_sources = cls._evidence_sources(
                prediction,
                seasonal_match,
                spatial_match,
                event_match,
                mobility_match,
                market_match,
                platform_match,
            )
            chain = {
                "correlation_id": f"CROSS-DIM-CORR-{len(chains) + 1:04d}",
                "season": seasonal_match.get("season_name") or mobility_match.get("season") or prediction.get("time_window", "needs_review"),
                "location": location,
                "event": event_name,
                "market": market,
                "platform": platform,
                "pain_cluster": pain_cluster,
                "mobility_demand": demand_type,
                "prediction": {
                    "prediction_id": prediction.get("prediction_id", "needs_review"),
                    "time_window": prediction.get("time_window", "needs_review"),
                    "predicted_heat_score": prediction.get("predicted_heat_score", 0),
                    "confidence_score": prediction.get("confidence_score", 0),
                    "prediction_dimension": prediction.get("prediction_dimension", "needs_review"),
                },
                "why_correlated": cls._why_correlated(
                    prediction,
                    seasonal_match,
                    spatial_match,
                    event_match,
                    market_match,
                    platform_match,
                    pain_cluster,
                    demand_type,
                ),
                "evidence_sources": evidence_sources,
                "confidence_score": confidence,
                "recommended_strategy_type": strategy_type,
                "human_review_required": True,
                "auto_publish_allowed": False,
                "auto_reply_allowed": False,
                "auto_contact_allowed": False,
                "auto_dispatch_allowed": False,
                "auto_quote_allowed": False,
                "write_api_allowed": False,
                "sample_data_only": True,
                "confirmed_real_business_result": False,
            }
            chains.append(chain)
            if len(chains) >= 24:
                break
        return sorted(chains, key=lambda row: (-row["confidence_score"], -int(row["prediction"].get("predicted_heat_score", 0))))

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
    def _mobility_index(mobility: list[dict[str, Any]]) -> dict[tuple[str, str, str, str], dict[str, Any]]:
        result: dict[tuple[str, str, str, str], dict[str, Any]] = {}
        for item in mobility:
            key = (
                item.get("market", ""),
                item.get("location", ""),
                item.get("event", ""),
                item.get("demand_type", ""),
            )
            result[key] = item
            result.setdefault((item.get("market", ""), item.get("location", ""), "*", item.get("demand_type", "")), item)
            result.setdefault(("*", item.get("location", ""), "*", item.get("demand_type", "")), item)
        return result

    @staticmethod
    def _match_mobility(
        prediction: dict[str, Any],
        mobility_index: dict[tuple[str, str, str, str], dict[str, Any]],
    ) -> dict[str, Any]:
        market = prediction.get("market", "")
        location = prediction.get("location", "")
        event_name = prediction.get("event", "")
        demand_type = prediction.get("demand_type", "")
        return (
            mobility_index.get((market, location, event_name, demand_type))
            or mobility_index.get((market, location, "*", demand_type))
            or mobility_index.get(("*", location, "*", demand_type))
            or {}
        )

    @staticmethod
    def _match_season(
        prediction: dict[str, Any],
        seasonal: list[dict[str, Any]],
        mobility_match: dict[str, Any],
    ) -> dict[str, Any]:
        market = prediction.get("market", "")
        location = prediction.get("location", "")
        season_name = mobility_match.get("season", "")
        time_window = prediction.get("time_window", "")
        for item in seasonal:
            if market and item.get("market") != market:
                continue
            if season_name and item.get("season_name") == season_name:
                return item
            if location and location in item.get("likely_locations", []):
                return item
            if time_window and time_window == item.get("time_window"):
                return item
        for item in seasonal:
            if location and location in item.get("likely_locations", []):
                return item
        return seasonal[0] if seasonal else {}

    @staticmethod
    def _platform(
        market_match: dict[str, Any],
        platform_index: dict[str, dict[str, Any]],
        demand_type: str,
    ) -> str:
        preferences = market_match.get("platform_preference", [])
        if preferences:
            preferred = preferences[0].get("platform")
            if preferred:
                return preferred
        if demand_type in {"airport transfer", "private charter", "hotel transfer"}:
            return "SEO / Search" if "SEO / Search" in platform_index else "Reddit"
        return next(iter(platform_index.keys()), "Reddit")

    @staticmethod
    def _pain_cluster(
        seasonal_match: dict[str, Any],
        spatial_match: dict[str, Any],
        platform_match: dict[str, Any],
        market_match: dict[str, Any],
        prediction: dict[str, Any],
    ) -> str:
        for source in (
            seasonal_match.get("pain_clusters", []),
            spatial_match.get("pain_clusters", []),
            platform_match.get("dominant_pain_points", []),
            market_match.get("dominant_pain_points", []),
        ):
            if source:
                return source[0]
        return prediction.get("demand_type", "needs_review")

    @staticmethod
    def _confidence(
        prediction: dict[str, Any],
        seasonal_match: dict[str, Any],
        spatial_match: dict[str, Any],
        event_match: dict[str, Any],
        mobility_match: dict[str, Any],
        market_match: dict[str, Any],
        platform_match: dict[str, Any],
    ) -> int:
        scores = [
            int(prediction.get("confidence_score", 0)),
            int(seasonal_match.get("confidence_score", 55)),
            int(spatial_match.get("confidence_score", 55)),
            int(event_match.get("confidence_score", 52)) if event_match else 52,
            int(mobility_match.get("intent_strength", 55)),
            int(market_match.get("opportunity_score", 55)),
            max(50, 82 - (12 if platform_match.get("promotion_risk") == "high" else 0)),
        ]
        return max(0, min(100, round(sum(scores) / len(scores))))

    @staticmethod
    def _strategy_type(demand_type: str, event_name: str, location: str, platform: str) -> str:
        if demand_type in {"airport transfer", "hotel transfer", "night arrival"}:
            return "driver_operation_strategy"
        if demand_type in {"event pickup", "multi-city route"} or (event_name and event_name != "none"):
            return "event_response_strategy"
        if demand_type in {"private charter", "family trip", "sightseeing route", "elderly support"}:
            return "local_business_strategy"
        if platform in {"Reddit", "SEO / Search", "YouTube", "Xiaohongshu"}:
            return "platform_content_strategy"
        if location and location != "needs_review":
            return "spatial_monitoring_strategy"
        return "monitor_only"

    @staticmethod
    def _evidence_sources(
        prediction: dict[str, Any],
        seasonal_match: dict[str, Any],
        spatial_match: dict[str, Any],
        event_match: dict[str, Any],
        mobility_match: dict[str, Any],
        market_match: dict[str, Any],
        platform_match: dict[str, Any],
    ) -> list[str]:
        evidence = list(prediction.get("evidence_sources", []))
        if seasonal_match.get("season_id"):
            evidence.append(f"seasonal_intelligence:{seasonal_match['season_id']}")
        if spatial_match.get("location_id"):
            evidence.append(f"spatial_intelligence:{spatial_match['location_id']}")
        if event_match.get("event_id"):
            evidence.append(f"event_intelligence:{event_match['event_id']}")
        if mobility_match.get("mobility_id"):
            evidence.append(f"mobility_intelligence:{mobility_match['mobility_id']}")
        if market_match.get("market"):
            evidence.append(f"market_intelligence:{market_match['market']}")
        if platform_match.get("platform"):
            evidence.append(f"platform_pain_intelligence:{platform_match['platform']}")
        return list(dict.fromkeys(evidence))

    @staticmethod
    def _why_correlated(
        prediction: dict[str, Any],
        seasonal_match: dict[str, Any],
        spatial_match: dict[str, Any],
        event_match: dict[str, Any],
        market_match: dict[str, Any],
        platform_match: dict[str, Any],
        pain_cluster: str,
        demand_type: str,
    ) -> str:
        season = seasonal_match.get("season_name") or prediction.get("time_window", "the current time window")
        location = prediction.get("location", "the target location")
        market = prediction.get("market", "the target market")
        platform = platform_match.get("platform", "the platform")
        event = event_match.get("event_name") or prediction.get("event", "no specific event")
        heat = prediction.get("predicted_heat_score", 0)
        market_need = market_match.get("mobility_need", "mobility need requires review")
        return (
            f"{season} points to {location}, {event} adds short-term pressure, {market} has {market_need}, "
            f"and {platform} expresses the pain as {pain_cluster}; together this supports {demand_type} with heat {heat}."
        )

    @staticmethod
    def _heatmap(chains: list[dict[str, Any]]) -> list[dict[str, Any]]:
        grouped: dict[tuple[str, str, str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
        for chain in chains:
            key = (
                chain["season"],
                chain["location"],
                chain["event"],
                chain["market"],
                chain["platform"],
                chain["mobility_demand"],
            )
            grouped[key].append(chain)
        heatmap = []
        for index, (key, rows) in enumerate(grouped.items(), start=1):
            season, location, event, market, platform, mobility_demand = key
            avg_confidence = round(sum(row["confidence_score"] for row in rows) / len(rows))
            avg_heat = round(sum(int(row["prediction"].get("predicted_heat_score", 0)) for row in rows) / len(rows))
            heatmap.append(
                {
                    "heatmap_id": f"CROSS-DIM-HEAT-{index:04d}",
                    "season": season,
                    "location": location,
                    "event": event,
                    "market": market,
                    "platform": platform,
                    "mobility_demand": mobility_demand,
                    "chain_count": len(rows),
                    "average_confidence_score": avg_confidence,
                    "average_predicted_heat_score": avg_heat,
                    "human_review_required": True,
                    "auto_action_allowed": False,
                }
            )
        return sorted(heatmap, key=lambda row: (-row["average_predicted_heat_score"], -row["average_confidence_score"]))

    @staticmethod
    def _strategy_candidates(chains: list[dict[str, Any]]) -> list[dict[str, Any]]:
        rows = []
        for index, chain in enumerate(chains[:16], start=1):
            rows.append(
                {
                    "strategy_signal_id": f"STRATEGY-SIGNAL-{index:04d}",
                    "correlation_id": chain["correlation_id"],
                    "recommended_strategy_type": chain["recommended_strategy_type"],
                    "market": chain["market"],
                    "platform": chain["platform"],
                    "location": chain["location"],
                    "mobility_demand": chain["mobility_demand"],
                    "confidence_score": chain["confidence_score"],
                    "why_candidate": chain["why_correlated"],
                    "human_review_required": True,
                    "auto_publish_allowed": False,
                    "auto_contact_allowed": False,
                    "auto_dispatch_allowed": False,
                    "auto_quote_allowed": False,
                    "write_api_allowed": False,
                }
            )
        return rows

    @staticmethod
    def _summary(
        chains: list[dict[str, Any]],
        heatmap: list[dict[str, Any]],
        strategy_candidates: list[dict[str, Any]],
    ) -> dict[str, Any]:
        strategy_counts = Counter(item["recommended_strategy_type"] for item in chains)
        markets = sorted({item["market"] for item in chains})
        platforms = sorted({item["platform"] for item in chains})
        return {
            "cross_dimensional_correlation_ready": bool(chains),
            "correlation_chain_count": len(chains),
            "heatmap_row_count": len(heatmap),
            "strategy_candidate_count": len(strategy_candidates),
            "markets": markets,
            "platforms": platforms,
            "strategy_type_counts": dict(strategy_counts),
            "all_chains_human_review_required": all(item.get("human_review_required") is True for item in chains),
            "all_strategy_candidates_human_review_required": all(
                item.get("human_review_required") is True for item in strategy_candidates
            ),
            "sample_data_only": True,
            "auto_publish_allowed": False,
            "auto_reply_allowed": False,
            "auto_contact_allowed": False,
            "auto_dispatch_allowed": False,
            "auto_quote_allowed": False,
            "write_api_allowed": False,
            "next_recommendation": "Use reviewed correlation chains to choose content, local business, or driver operation strategy candidates; keep every action human-gated.",
        }


if __name__ == "__main__":
    report = CrossDimensionalCorrelation().build()
    print(json.dumps(report["crossDimensionalCorrelationSummary"], ensure_ascii=False, indent=2, sort_keys=True))
