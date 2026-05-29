"""Market intelligence matrix for global AGOS intelligence."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from services.global_batch_intelligence_collection import GlobalBatchIntelligenceCollection
from services.global_pain_cluster_engine import GlobalPainClusterEngine
from services.platform_pain_intelligence import PlatformPainIntelligence
from services.runtime_persistence import utc_now_iso


DEFAULT_RECORDS_PATH = Path("runtime/global_batch_intelligence_collection/global_intelligence_records.json")
DEFAULT_CLUSTERS_PATH = Path("runtime/global_pain_clusters/global_pain_clusters.json")
DEFAULT_PLATFORM_PROFILES_PATH = Path("runtime/platform_pain_intelligence/platform_pain_profiles.json")
DEFAULT_OUTPUT_DIR = Path("runtime/market_intelligence_matrix")

SUPPORTED_MARKETS = [
    "Japan",
    "US",
    "Europe",
    "Korea",
    "Taiwan",
    "Southeast Asia",
    "China outbound",
]

MARKET_RULES = {
    "Japan": {
        "travel_style": "domestic precision, punctuality, station detail, local convenience",
        "mobility_need": "station-to-hotel, airport transfer, complex urban transfer",
        "trust_barrier": "expects precise route and reliability; avoids vague claims",
        "price_sensitivity": "medium",
        "content_tone": "calm, precise, local, non-exaggerated",
        "conversion_risk": "medium",
        "opportunity_base": 72,
    },
    "US": {
        "travel_style": "independent planning, convenience-driven, review-aware",
        "mobility_need": "airport transfer, family trip, luggage-heavy private movement",
        "trust_barrier": "needs proof, reviews, transparent pricing, and safety context",
        "price_sensitivity": "medium",
        "content_tone": "direct, practical, proof-backed",
        "conversion_risk": "medium",
        "opportunity_base": 76,
    },
    "Europe": {
        "travel_style": "multi-city planning, rail-aware, value and reliability balanced",
        "mobility_need": "multi-city transfer, station-to-hotel, airport pickup",
        "trust_barrier": "skeptical of tourist traps and unclear inclusions",
        "price_sensitivity": "high",
        "content_tone": "transparent, comparative, understated",
        "conversion_risk": "medium",
        "opportunity_base": 74,
    },
    "Korea": {
        "travel_style": "visual planning, trend-sensitive, compact itinerary",
        "mobility_need": "airport transfer, family route, shopping and luggage support",
        "trust_barrier": "needs social proof, clean visuals, and clear Korean-language guidance",
        "price_sensitivity": "medium",
        "content_tone": "visual, concise, stylish, reassuring",
        "conversion_risk": "medium",
        "opportunity_base": 78,
    },
    "Taiwan": {
        "travel_style": "life-oriented, relaxed itinerary, family and small-group friendly",
        "mobility_need": "private charter, family trip, luggage-heavy sightseeing route",
        "trust_barrier": "needs warm tone, practical itinerary examples, and low-pressure CTA",
        "price_sensitivity": "medium",
        "content_tone": "friendly, practical, life-style, low pressure",
        "conversion_risk": "low",
        "opportunity_base": 80,
    },
    "Southeast Asia": {
        "travel_style": "mobile-first, deal-aware, group and family planning",
        "mobility_need": "airport transfer, group route, seasonal itinerary support",
        "trust_barrier": "needs price clarity, language simplicity, and fast response expectation",
        "price_sensitivity": "high",
        "content_tone": "simple, helpful, mobile-first, clear value",
        "conversion_risk": "medium",
        "opportunity_base": 75,
    },
    "China outbound": {
        "travel_style": "outbound planning, platform-specific note-taking, family and shopping routes",
        "mobility_need": "airport pickup, private charter, luggage-heavy shopping route",
        "trust_barrier": "needs Mandarin clarity, local proof, and strict claim control",
        "price_sensitivity": "medium",
        "content_tone": "practical, note-style, trust-building, avoid overclaiming",
        "conversion_risk": "high",
        "opportunity_base": 77,
    },
}


class MarketIntelligenceMatrix:
    """Build market-level intelligence without creating promotion actions."""

    def __init__(
        self,
        records_path: str | Path = DEFAULT_RECORDS_PATH,
        clusters_path: str | Path = DEFAULT_CLUSTERS_PATH,
        platform_profiles_path: str | Path = DEFAULT_PLATFORM_PROFILES_PATH,
        output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    ) -> None:
        self.records_path = Path(records_path)
        self.clusters_path = Path(clusters_path)
        self.platform_profiles_path = Path(platform_profiles_path)
        self.output_dir = Path(output_dir)
        self.report_path = self.output_dir / "MARKET_INTELLIGENCE_MATRIX_REPORT.json"
        self.matrix_path = self.output_dir / "market_intelligence_matrix.json"
        self.platform_fit_path = self.output_dir / "market_platform_fit.json"
        self.pain_ranking_path = self.output_dir / "market_pain_ranking.json"
        self.summary_path = self.output_dir / "market_intelligence_summary.json"

    def build(
        self,
        records: list[dict[str, Any]] | None = None,
        clusters: list[dict[str, Any]] | None = None,
        platform_profiles: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        source_records = records if records is not None else self._load_records()
        source_clusters = clusters if clusters is not None else self._load_clusters()
        source_platform_profiles = platform_profiles if platform_profiles is not None else self._load_platform_profiles()
        matrix = [self._market_profile(market, source_records, source_clusters, source_platform_profiles) for market in SUPPORTED_MARKETS]
        platform_fit = self._platform_fit(matrix, source_platform_profiles)
        pain_ranking = self._pain_ranking(matrix)
        summary = self._summary(matrix)
        report = {
            "report_id": "MARKET_INTELLIGENCE_MATRIX_REPORT",
            "round_id": "ROUND-GLOBAL-004",
            "created_at": utc_now_iso(),
            "status": "market_intelligence_matrix_ready",
            "phase": "GLOBAL_INTELLIGENCE_COLLECTION",
            "marketIntelligenceMatrix": matrix,
            "marketPlatformFit": platform_fit,
            "marketPainRanking": pain_ranking,
            "marketIntelligenceSummary": summary,
            "safetyBoundary": "Market Intelligence Matrix builds market-level analysis only. It does not generate automatic promotion actions, publish, reply, contact users, or call platform write APIs.",
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
        self.matrix_path.write_text(json.dumps(report["marketIntelligenceMatrix"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.platform_fit_path.write_text(json.dumps(report["marketPlatformFit"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.pain_ranking_path.write_text(json.dumps(report["marketPainRanking"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.summary_path.write_text(json.dumps(report["marketIntelligenceSummary"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    def _load_records(self) -> list[dict[str, Any]]:
        if not self.records_path.exists():
            GlobalBatchIntelligenceCollection().collect()
        payload = json.loads(self.records_path.read_text(encoding="utf-8")) if self.records_path.exists() else []
        return payload if isinstance(payload, list) else []

    def _load_clusters(self) -> list[dict[str, Any]]:
        if not self.clusters_path.exists():
            GlobalPainClusterEngine().build()
        payload = json.loads(self.clusters_path.read_text(encoding="utf-8")) if self.clusters_path.exists() else []
        return payload if isinstance(payload, list) else []

    def _load_platform_profiles(self) -> list[dict[str, Any]]:
        if not self.platform_profiles_path.exists():
            PlatformPainIntelligence().build()
        payload = json.loads(self.platform_profiles_path.read_text(encoding="utf-8")) if self.platform_profiles_path.exists() else []
        return payload if isinstance(payload, list) else []

    @staticmethod
    def _market_profile(
        market: str,
        records: list[dict[str, Any]],
        clusters: list[dict[str, Any]],
        platform_profiles: list[dict[str, Any]],
    ) -> dict[str, Any]:
        market_records = [item for item in records if item.get("market") == market]
        languages = sorted({item.get("language", "unknown") for item in market_records}) or ["needs_review"]
        topic_counts = Counter(item.get("topic", "unknown") for item in market_records)
        platform_counts = Counter(item.get("source_platform", "unknown") for item in market_records)
        cluster_by_key = {item.get("cluster_key"): item for item in clusters}
        dominant_pain_points: list[str] = []
        for topic, _ in topic_counts.most_common(4):
            dominant_pain_points.extend(cluster_by_key.get(topic, {}).get("pain_points", [topic])[:2])
        rules = MARKET_RULES[market]
        platform_preference = MarketIntelligenceMatrix._platform_preference(market, platform_counts, platform_profiles)
        score = min(100, rules["opportunity_base"] + len(market_records) * 2 + len(dominant_pain_points))
        return {
            "market": market,
            "languages": languages,
            "dominant_pain_points": list(dict.fromkeys(dominant_pain_points))[:6],
            "travel_style": rules["travel_style"],
            "mobility_need": rules["mobility_need"],
            "trust_barrier": rules["trust_barrier"],
            "price_sensitivity": rules["price_sensitivity"],
            "platform_preference": platform_preference,
            "content_tone": rules["content_tone"],
            "conversion_risk": rules["conversion_risk"],
            "opportunity_score": score,
            "source_record_ids": [item.get("record_id", "") for item in market_records if item.get("record_id")],
            "record_count": len(market_records),
            "market_isolation_key": market,
            "human_review_required": True,
            "auto_promotion_allowed": False,
            "auto_reply_allowed": False,
            "write_api_allowed": False,
        }

    @staticmethod
    def _platform_preference(
        market: str,
        platform_counts: Counter[str],
        platform_profiles: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        default_preferences = {
            "Japan": ["SEO / Search", "YouTube", "X"],
            "US": ["Reddit", "YouTube", "SEO / Search"],
            "Europe": ["SEO / Search", "Reddit", "YouTube"],
            "Korea": ["Instagram", "TikTok", "YouTube"],
            "Taiwan": ["Instagram", "YouTube", "SEO / Search"],
            "Southeast Asia": ["TikTok", "Instagram", "YouTube"],
            "China outbound": ["Xiaohongshu", "SEO / Search", "TikTok"],
        }
        risk_by_platform = {item["platform"]: item.get("promotion_risk", "medium") for item in platform_profiles}
        ranked = [platform for platform, _ in platform_counts.most_common()]
        for platform in default_preferences[market]:
            if platform not in ranked:
                ranked.append(platform)
        return [
            {
                "platform": platform,
                "fit_reason": f"{market} demand can use {platform} for platform-aware discovery or education.",
                "promotion_risk": risk_by_platform.get(platform, "medium"),
                "human_review_required": True,
            }
            for platform in ranked[:4]
        ]

    @staticmethod
    def _platform_fit(matrix: list[dict[str, Any]], platform_profiles: list[dict[str, Any]]) -> list[dict[str, Any]]:
        profile_by_platform = {item["platform"]: item for item in platform_profiles}
        rows = []
        for item in matrix:
            for preference in item["platform_preference"]:
                profile = profile_by_platform.get(preference["platform"], {})
                rows.append(
                    {
                        "market": item["market"],
                        "platform": preference["platform"],
                        "content_tone": item["content_tone"],
                        "content_format_fit": profile.get("content_format_fit", "needs_review"),
                        "promotion_risk": preference["promotion_risk"],
                        "safe_cta_style": profile.get("safe_cta_style", "needs_review"),
                        "human_review_required": True,
                    }
                )
        return rows

    @staticmethod
    def _pain_ranking(matrix: list[dict[str, Any]]) -> list[dict[str, Any]]:
        rows = []
        for item in matrix:
            for rank, pain in enumerate(item["dominant_pain_points"], start=1):
                rows.append(
                    {
                        "market": item["market"],
                        "rank": rank,
                        "pain_point": pain,
                        "opportunity_score": max(0, item["opportunity_score"] - rank),
                        "conversion_risk": item["conversion_risk"],
                        "human_review_required": True,
                    }
                )
        return rows

    @staticmethod
    def _summary(matrix: list[dict[str, Any]]) -> dict[str, Any]:
        top_markets = sorted(matrix, key=lambda item: item["opportunity_score"], reverse=True)
        china = next(item for item in matrix if item["market"] == "China outbound")
        japan = next(item for item in matrix if item["market"] == "Japan")
        return {
            "market_intelligence_matrix_ready": True,
            "market_count": len(matrix),
            "top_opportunity_markets": [item["market"] for item in top_markets[:5]],
            "highest_opportunity_score": top_markets[0]["opportunity_score"] if top_markets else 0,
            "all_markets_human_review_required": all(item["human_review_required"] for item in matrix),
            "auto_promotion_allowed": False,
            "auto_reply_allowed": False,
            "write_api_allowed": False,
            "china_outbound_isolation_key": china["market_isolation_key"],
            "japan_isolation_key": japan["market_isolation_key"],
            "china_outbound_pollutes_japan_local": china["market_isolation_key"] == japan["market_isolation_key"],
            "next_recommendation": "Use market matrix for Cross-Platform Correlation Expansion after human review.",
        }


if __name__ == "__main__":
    result = MarketIntelligenceMatrix().build()
    print(json.dumps({"status": result["status"], "summary": result["marketIntelligenceSummary"]}, indent=2))
