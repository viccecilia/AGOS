"""Cross-platform correlation expansion for AGOS global intelligence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.global_pain_cluster_engine import GlobalPainClusterEngine
from services.market_intelligence_matrix import MarketIntelligenceMatrix
from services.platform_pain_intelligence import PlatformPainIntelligence
from services.runtime_persistence import utc_now_iso


DEFAULT_PLATFORM_PROFILES_PATH = Path("runtime/platform_pain_intelligence/platform_pain_profiles.json")
DEFAULT_MARKET_MATRIX_PATH = Path("runtime/market_intelligence_matrix/market_intelligence_matrix.json")
DEFAULT_CLUSTERS_PATH = Path("runtime/global_pain_clusters/global_pain_clusters.json")
DEFAULT_OUTPUT_DIR = Path("runtime/cross_platform_correlation")

EXPANSION_RULES = [
    {
        "source_platform": "Reddit",
        "target_platforms": ["TikTok", "YouTube", "SEO / Search"],
        "content_expansion_fit": "Turn detailed pain question into short hook, explainer, and search FAQ.",
        "risk_level": "high",
    },
    {
        "source_platform": "TikTok",
        "target_platforms": ["SEO / Search", "Instagram", "X"],
        "content_expansion_fit": "Turn trend hook into search topic, saveable carousel, and quick signal post.",
        "risk_level": "medium",
    },
    {
        "source_platform": "YouTube",
        "target_platforms": ["X", "SEO / Search", "Threads"],
        "content_expansion_fit": "Turn comment pain into short post, FAQ section, and community discussion.",
        "risk_level": "medium",
    },
    {
        "source_platform": "Xiaohongshu",
        "target_platforms": ["Instagram", "TikTok", "SEO / Search"],
        "content_expansion_fit": "Turn note-style experience into carousel, short video angle, and search guide.",
        "risk_level": "medium",
    },
    {
        "source_platform": "SEO / Search",
        "target_platforms": ["Reddit", "YouTube", "Threads"],
        "content_expansion_fit": "Turn search intent into question-led reply, explainer, and discussion starter.",
        "risk_level": "medium",
    },
    {
        "source_platform": "Instagram",
        "target_platforms": ["Xiaohongshu", "TikTok", "YouTube"],
        "content_expansion_fit": "Turn saveable visual guide into note, short hook, and route explainer.",
        "risk_level": "medium",
    },
    {
        "source_platform": "X",
        "target_platforms": ["Reddit", "Threads", "SEO / Search"],
        "content_expansion_fit": "Turn quick signal into discussion, community post, and search article idea.",
        "risk_level": "medium",
    },
    {
        "source_platform": "Threads",
        "target_platforms": ["Instagram", "X", "Reddit"],
        "content_expansion_fit": "Turn casual discussion into carousel, concise post, and detailed question.",
        "risk_level": "low",
    },
]


class CrossPlatformCorrelationExpansion:
    """Find cross-platform expansion opportunities without creating publish tasks."""

    def __init__(
        self,
        platform_profiles_path: str | Path = DEFAULT_PLATFORM_PROFILES_PATH,
        market_matrix_path: str | Path = DEFAULT_MARKET_MATRIX_PATH,
        clusters_path: str | Path = DEFAULT_CLUSTERS_PATH,
        output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    ) -> None:
        self.platform_profiles_path = Path(platform_profiles_path)
        self.market_matrix_path = Path(market_matrix_path)
        self.clusters_path = Path(clusters_path)
        self.output_dir = Path(output_dir)
        self.report_path = self.output_dir / "CROSS_PLATFORM_CORRELATION_REPORT.json"
        self.correlations_path = self.output_dir / "cross_platform_correlations.json"
        self.map_path = self.output_dir / "platform_expansion_map.json"
        self.risk_path = self.output_dir / "correlation_risk_review.json"
        self.summary_path = self.output_dir / "cross_platform_correlation_summary.json"

    def build(
        self,
        platform_profiles: list[dict[str, Any]] | None = None,
        market_matrix: list[dict[str, Any]] | None = None,
        clusters: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        source_profiles = platform_profiles if platform_profiles is not None else self._load_platform_profiles()
        source_markets = market_matrix if market_matrix is not None else self._load_market_matrix()
        source_clusters = clusters if clusters is not None else self._load_clusters()
        correlations = self._correlations(source_profiles, source_markets, source_clusters)
        expansion_map = self._expansion_map(correlations)
        risk_review = self._risk_review(correlations)
        summary = self._summary(correlations)
        report = {
            "report_id": "CROSS_PLATFORM_CORRELATION_REPORT",
            "round_id": "ROUND-GLOBAL-005",
            "created_at": utc_now_iso(),
            "status": "cross_platform_correlation_ready",
            "phase": "GLOBAL_INTELLIGENCE_COLLECTION",
            "crossPlatformCorrelations": correlations,
            "platformExpansionMap": expansion_map,
            "correlationRiskReview": risk_review,
            "crossPlatformCorrelationSummary": summary,
            "safetyBoundary": "Cross-Platform Correlation Expansion identifies expansion opportunities only. It does not generate publish tasks, auto-post, auto-reply, contact users, or call platform write APIs.",
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
        self.correlations_path.write_text(json.dumps(report["crossPlatformCorrelations"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.map_path.write_text(json.dumps(report["platformExpansionMap"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.risk_path.write_text(json.dumps(report["correlationRiskReview"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.summary_path.write_text(json.dumps(report["crossPlatformCorrelationSummary"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    def _load_platform_profiles(self) -> list[dict[str, Any]]:
        if not self.platform_profiles_path.exists():
            PlatformPainIntelligence().build()
        payload = json.loads(self.platform_profiles_path.read_text(encoding="utf-8")) if self.platform_profiles_path.exists() else []
        return payload if isinstance(payload, list) else []

    def _load_market_matrix(self) -> list[dict[str, Any]]:
        if not self.market_matrix_path.exists():
            MarketIntelligenceMatrix().build()
        payload = json.loads(self.market_matrix_path.read_text(encoding="utf-8")) if self.market_matrix_path.exists() else []
        return payload if isinstance(payload, list) else []

    def _load_clusters(self) -> list[dict[str, Any]]:
        if not self.clusters_path.exists():
            GlobalPainClusterEngine().build()
        payload = json.loads(self.clusters_path.read_text(encoding="utf-8")) if self.clusters_path.exists() else []
        return payload if isinstance(payload, list) else []

    @staticmethod
    def _correlations(
        platform_profiles: list[dict[str, Any]],
        market_matrix: list[dict[str, Any]],
        clusters: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        profile_by_platform = {item["platform"]: item for item in platform_profiles}
        clusters_by_platform = {
            platform: [cluster for cluster in clusters if platform in cluster.get("platforms", [])]
            for platform in profile_by_platform
        }
        correlations = []
        index = 1
        for rule in EXPANSION_RULES:
            source = rule["source_platform"]
            profile = profile_by_platform.get(source)
            if not profile:
                continue
            source_clusters = clusters_by_platform.get(source) or clusters[:1]
            cluster = source_clusters[0] if source_clusters else {}
            market = CrossPlatformCorrelationExpansion._best_market(source, market_matrix)
            source_pain = (profile.get("dominant_pain_points") or cluster.get("pain_points") or ["needs_review"])[0]
            risk_level = CrossPlatformCorrelationExpansion._risk_level(rule["risk_level"], profile)
            correlations.append(
                {
                    "correlation_id": f"CROSS-PLATFORM-CORR-{index:03d}",
                    "source_platform": source,
                    "target_platforms": rule["target_platforms"],
                    "source_pain": source_pain,
                    "source_cluster_id": cluster.get("cluster_id", "needs_review"),
                    "market": market,
                    "why_correlated": CrossPlatformCorrelationExpansion._why_correlated(source, rule["target_platforms"], source_pain, market),
                    "content_expansion_fit": rule["content_expansion_fit"],
                    "risk_level": risk_level,
                    "human_review_required": True,
                    "auto_publish_allowed": False,
                    "auto_reply_allowed": False,
                    "publish_task_created": False,
                    "write_api_allowed": False,
                }
            )
            index += 1
        return correlations

    @staticmethod
    def _best_market(source_platform: str, market_matrix: list[dict[str, Any]]) -> str:
        for item in sorted(market_matrix, key=lambda row: row.get("opportunity_score", 0), reverse=True):
            if any(pref.get("platform") == source_platform for pref in item.get("platform_preference", [])):
                return item["market"]
        return market_matrix[0]["market"] if market_matrix else "needs_review"

    @staticmethod
    def _risk_level(base: str, profile: dict[str, Any]) -> str:
        if profile.get("promotion_risk") == "high":
            return "high"
        if base == "high":
            return "high"
        if profile.get("reply_risk") == "medium" or base == "medium":
            return "medium"
        return "low"

    @staticmethod
    def _why_correlated(source_platform: str, targets: list[str], source_pain: str, market: str) -> str:
        return (
            f"{source_platform} captures '{source_pain}' in {market}; "
            f"the same pain can be reframed for {', '.join(targets)} with platform-specific format and safer CTA."
        )

    @staticmethod
    def _expansion_map(correlations: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "source_platform": item["source_platform"],
                "target_platforms": item["target_platforms"],
                "market": item["market"],
                "risk_level": item["risk_level"],
                "human_review_required": item["human_review_required"],
                "auto_publish_allowed": item["auto_publish_allowed"],
            }
            for item in correlations
        ]

    @staticmethod
    def _risk_review(correlations: list[dict[str, Any]]) -> dict[str, Any]:
        high_risk = [item for item in correlations if item["risk_level"] == "high"]
        return {
            "human_review_required": True,
            "all_correlations_human_review_required": all(item["human_review_required"] for item in correlations),
            "auto_publish_allowed": False,
            "auto_reply_allowed": False,
            "publish_task_created": False,
            "write_api_allowed": False,
            "high_risk_correlation_count": len(high_risk),
            "high_risk_correlation_ids": [item["correlation_id"] for item in high_risk],
            "risk_note": "High-risk correlations are expansion ideas only and must not become publish tasks without explicit human review.",
        }

    @staticmethod
    def _summary(correlations: list[dict[str, Any]]) -> dict[str, Any]:
        platforms = sorted({item["source_platform"] for item in correlations})
        targets = sorted({target for item in correlations for target in item["target_platforms"]})
        high_risk = [item for item in correlations if item["risk_level"] == "high"]
        return {
            "cross_platform_correlation_ready": True,
            "correlation_count": len(correlations),
            "source_platform_count": len(platforms),
            "target_platform_count": len(targets),
            "high_risk_correlation_count": len(high_risk),
            "all_correlations_human_review_required": all(item["human_review_required"] for item in correlations),
            "auto_publish_allowed": False,
            "auto_reply_allowed": False,
            "publish_task_created": False,
            "write_api_allowed": False,
            "next_recommendation": "Use reviewed correlations for Intelligence Ranking and Noise Filtering; keep publishing blocked.",
        }


if __name__ == "__main__":
    result = CrossPlatformCorrelationExpansion().build()
    print(json.dumps({"status": result["status"], "summary": result["crossPlatformCorrelationSummary"]}, indent=2))
