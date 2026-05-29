"""Intelligence ranking and noise filtering for AGOS global intelligence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.cross_platform_correlation_expansion import CrossPlatformCorrelationExpansion
from services.global_pain_cluster_engine import GlobalPainClusterEngine
from services.market_intelligence_matrix import MarketIntelligenceMatrix
from services.platform_pain_intelligence import PlatformPainIntelligence
from services.runtime_persistence import utc_now_iso


DEFAULT_CLUSTERS_PATH = Path("runtime/global_pain_clusters/global_pain_clusters.json")
DEFAULT_PLATFORM_PROFILES_PATH = Path("runtime/platform_pain_intelligence/platform_pain_profiles.json")
DEFAULT_MARKET_MATRIX_PATH = Path("runtime/market_intelligence_matrix/market_intelligence_matrix.json")
DEFAULT_CORRELATIONS_PATH = Path("runtime/cross_platform_correlation/cross_platform_correlations.json")
DEFAULT_OUTPUT_DIR = Path("runtime/intelligence_ranking")

MOBILITY_TERMS = {
    "airport",
    "transfer",
    "luggage",
    "station",
    "hotel",
    "route",
    "transport",
    "subway",
    "family",
    "private",
    "charter",
    "pickup",
    "crowd",
    "mobility",
}


class IntelligenceRankingNoiseFilter:
    """Score global intelligence and separate useful signals from noise."""

    def __init__(
        self,
        clusters_path: str | Path = DEFAULT_CLUSTERS_PATH,
        platform_profiles_path: str | Path = DEFAULT_PLATFORM_PROFILES_PATH,
        market_matrix_path: str | Path = DEFAULT_MARKET_MATRIX_PATH,
        correlations_path: str | Path = DEFAULT_CORRELATIONS_PATH,
        output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    ) -> None:
        self.clusters_path = Path(clusters_path)
        self.platform_profiles_path = Path(platform_profiles_path)
        self.market_matrix_path = Path(market_matrix_path)
        self.correlations_path = Path(correlations_path)
        self.output_dir = Path(output_dir)
        self.report_path = self.output_dir / "INTELLIGENCE_RANKING_REPORT.json"
        self.ranked_path = self.output_dir / "ranked_intelligence.json"
        self.high_value_path = self.output_dir / "high_value_intelligence.json"
        self.noise_path = self.output_dir / "noise_filtered_signals.json"
        self.unsafe_path = self.output_dir / "unsafe_signals.json"
        self.summary_path = self.output_dir / "intelligence_ranking_summary.json"

    def build(
        self,
        clusters: list[dict[str, Any]] | None = None,
        platform_profiles: list[dict[str, Any]] | None = None,
        market_matrix: list[dict[str, Any]] | None = None,
        correlations: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        source_clusters = clusters if clusters is not None else self._load_clusters()
        source_profiles = platform_profiles if platform_profiles is not None else self._load_platform_profiles()
        source_markets = market_matrix if market_matrix is not None else self._load_market_matrix()
        source_correlations = correlations if correlations is not None else self._load_correlations()

        ranked = self._rank_intelligence(source_clusters, source_profiles, source_markets, source_correlations)
        high_value = [item for item in ranked if item["ranking_status"] == "high_value"]
        noise_filtered = [item for item in ranked if item["ranking_status"] in {"low_value", "noise"}]
        unsafe = [item for item in ranked if item["ranking_status"] == "unsafe"]
        summary = self._summary(ranked, high_value, noise_filtered, unsafe)

        report = {
            "report_id": "INTELLIGENCE_RANKING_REPORT",
            "round_id": "ROUND-GLOBAL-006",
            "created_at": utc_now_iso(),
            "status": "intelligence_ranking_ready",
            "phase": "GLOBAL_INTELLIGENCE_COLLECTION",
            "rankedIntelligence": ranked,
            "highValueIntelligence": high_value,
            "noiseFilteredSignals": noise_filtered,
            "unsafeSignals": unsafe,
            "intelligenceRankingSummary": summary,
            "safetyBoundary": "Intelligence Ranking & Noise Filtering scores read-only intelligence only. It does not create publish tasks, auto-post, auto-reply, contact users, or call platform write APIs.",
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
        self.ranked_path.write_text(json.dumps(report["rankedIntelligence"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.high_value_path.write_text(json.dumps(report["highValueIntelligence"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.noise_path.write_text(json.dumps(report["noiseFilteredSignals"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.unsafe_path.write_text(json.dumps(report["unsafeSignals"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.summary_path.write_text(json.dumps(report["intelligenceRankingSummary"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

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

    def _load_market_matrix(self) -> list[dict[str, Any]]:
        if not self.market_matrix_path.exists():
            MarketIntelligenceMatrix().build()
        payload = json.loads(self.market_matrix_path.read_text(encoding="utf-8")) if self.market_matrix_path.exists() else []
        return payload if isinstance(payload, list) else []

    def _load_correlations(self) -> list[dict[str, Any]]:
        if not self.correlations_path.exists():
            CrossPlatformCorrelationExpansion().build()
        payload = json.loads(self.correlations_path.read_text(encoding="utf-8")) if self.correlations_path.exists() else []
        return payload if isinstance(payload, list) else []

    @classmethod
    def _rank_intelligence(
        cls,
        clusters: list[dict[str, Any]],
        platform_profiles: list[dict[str, Any]],
        market_matrix: list[dict[str, Any]],
        correlations: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        clusters_by_id = {item.get("cluster_id"): item for item in clusters}
        profiles_by_platform = {item.get("platform"): item for item in platform_profiles}
        markets_by_name = {item.get("market"): item for item in market_matrix}
        ranked: list[dict[str, Any]] = []

        for index, correlation in enumerate(correlations, start=1):
            cluster = clusters_by_id.get(correlation.get("source_cluster_id"), {})
            profile = profiles_by_platform.get(correlation.get("source_platform"), {})
            market = markets_by_name.get(correlation.get("market"), {})
            ranked.append(cls._ranking_item(index, correlation, cluster, profile, market))

        for cluster in clusters:
            index = len(ranked) + 1
            platform = (cluster.get("platforms") or ["needs_review"])[0]
            market_name = (cluster.get("markets") or ["needs_review"])[0]
            profile = profiles_by_platform.get(platform, {})
            market = markets_by_name.get(market_name, {})
            synthetic_correlation = {
                "correlation_id": cluster.get("cluster_id", f"CLUSTER-{index:03d}"),
                "source_platform": platform,
                "target_platforms": [],
                "source_pain": (cluster.get("pain_points") or [cluster.get("cluster_name", "needs_review")])[0],
                "source_cluster_id": cluster.get("cluster_id", "needs_review"),
                "market": market_name,
                "risk_level": "medium",
                "content_expansion_fit": "Pain cluster is evaluated as an intelligence signal before any action plan.",
            }
            ranked.append(cls._ranking_item(index, synthetic_correlation, cluster, profile, market, source_type="pain_cluster"))

        ranked.append(cls._noise_item(len(ranked) + 1))
        return sorted(ranked, key=lambda item: item["total_score"], reverse=True)

    @classmethod
    def _ranking_item(
        cls,
        index: int,
        signal: dict[str, Any],
        cluster: dict[str, Any],
        profile: dict[str, Any],
        market: dict[str, Any],
        source_type: str = "cross_platform_correlation",
    ) -> dict[str, Any]:
        risk_level = signal.get("risk_level", "medium")
        score_breakdown = {
            "pain_strength": cls._clip(cluster.get("business_relevance_score", 68)),
            "frequency": cls._clip(cluster.get("frequency_score", 60)),
            "emotion_intensity": cls._clip(cluster.get("emotion_intensity_score", 58)),
            "market_value": cls._clip(market.get("opportunity_score", 58)),
            "platform_fit": cls._platform_fit(signal.get("source_platform", ""), market, profile),
            "mobility_relevance": cls._mobility_relevance(cluster, signal),
            "conversion_potential": cls._conversion_potential(market, cluster, signal),
            "risk_level": cls._risk_score(risk_level),
            "evidence_confidence": cls._evidence_confidence(cluster, signal),
        }
        total_score = round(sum(score_breakdown.values()) / len(score_breakdown), 1)
        ranking_status = cls._status(total_score, risk_level, score_breakdown)
        noise_reason = cls._noise_reason(ranking_status, risk_level, score_breakdown)
        return {
            "intelligence_id": f"INTEL-RANK-{index:03d}",
            "source_type": source_type,
            "source_id": signal.get("correlation_id") or cluster.get("cluster_id", "needs_review"),
            "market": signal.get("market") or (cluster.get("markets") or ["needs_review"])[0],
            "platform": signal.get("source_platform") or (cluster.get("platforms") or ["needs_review"])[0],
            "target_platforms": signal.get("target_platforms", []),
            "pain_cluster": cluster.get("cluster_name") or signal.get("source_pain", "needs_review"),
            "pain_cluster_id": cluster.get("cluster_id", signal.get("source_cluster_id", "needs_review")),
            "source_pain": signal.get("source_pain", "needs_review"),
            "score_breakdown": score_breakdown,
            "total_score": total_score,
            "ranking_status": ranking_status,
            "noise_reason": noise_reason,
            "recommended_next_step": cls._next_step(ranking_status),
            "human_review_required": True,
            "auto_action_allowed": False,
            "auto_execute_allowed": False,
            "auto_publish_allowed": False,
            "auto_reply_allowed": False,
            "write_api_allowed": False,
            "unsafe_enters_action": False if ranking_status == "unsafe" else None,
            "evidence_summary": {
                "source_record_ids": cluster.get("source_record_ids", []),
                "content_expansion_fit": signal.get("content_expansion_fit", ""),
                "sample_or_read_only": True,
            },
        }

    @staticmethod
    def _noise_item(index: int) -> dict[str, Any]:
        return {
            "intelligence_id": f"INTEL-RANK-{index:03d}",
            "source_type": "noise_candidate",
            "source_id": "NOISE-SAMPLE-001",
            "market": "Global English",
            "platform": "unknown",
            "target_platforms": [],
            "pain_cluster": "generic travel chatter",
            "pain_cluster_id": "noise_sample",
            "source_pain": "nice photos and casual comments without mobility intent",
            "score_breakdown": {
                "pain_strength": 20,
                "frequency": 18,
                "emotion_intensity": 22,
                "market_value": 28,
                "platform_fit": 20,
                "mobility_relevance": 10,
                "conversion_potential": 16,
                "risk_level": 82,
                "evidence_confidence": 24,
            },
            "total_score": 26.7,
            "ranking_status": "noise",
            "noise_reason": "Low mobility relevance, weak evidence confidence, and no clear problem to solve.",
            "recommended_next_step": "Do not route into action. Keep only as a filtered noise example for review.",
            "human_review_required": True,
            "auto_action_allowed": False,
            "auto_execute_allowed": False,
            "auto_publish_allowed": False,
            "auto_reply_allowed": False,
            "write_api_allowed": False,
            "unsafe_enters_action": None,
            "evidence_summary": {
                "source_record_ids": [],
                "content_expansion_fit": "Not actionable.",
                "sample_or_read_only": True,
            },
        }

    @staticmethod
    def _clip(value: Any) -> int:
        try:
            return max(0, min(100, int(value)))
        except (TypeError, ValueError):
            return 0

    @classmethod
    def _platform_fit(cls, platform: str, market: dict[str, Any], profile: dict[str, Any]) -> int:
        preferred = {item.get("platform") for item in market.get("platform_preference", [])}
        base = 84 if platform in preferred else 62
        if profile.get("promotion_risk") == "high":
            base -= 12
        if profile.get("safe_cta_style"):
            base += 4
        return cls._clip(base)

    @classmethod
    def _mobility_relevance(cls, cluster: dict[str, Any], signal: dict[str, Any]) -> int:
        text = " ".join(
            [
                cluster.get("cluster_name", ""),
                signal.get("source_pain", ""),
                " ".join(cluster.get("pain_points", [])),
                signal.get("content_expansion_fit", ""),
            ]
        ).lower()
        hit_count = sum(1 for term in MOBILITY_TERMS if term in text)
        return cls._clip(38 + hit_count * 12)

    @classmethod
    def _conversion_potential(cls, market: dict[str, Any], cluster: dict[str, Any], signal: dict[str, Any]) -> int:
        market_score = cls._clip(market.get("opportunity_score", 55))
        relevance = cls._mobility_relevance(cluster, signal)
        frequency = cls._clip(cluster.get("frequency_score", 50))
        return cls._clip(round((market_score * 0.45) + (relevance * 0.35) + (frequency * 0.2)))

    @staticmethod
    def _risk_score(risk_level: str) -> int:
        return {"low": 88, "medium": 66, "high": 32}.get(risk_level, 54)

    @classmethod
    def _evidence_confidence(cls, cluster: dict[str, Any], signal: dict[str, Any]) -> int:
        source_count = len(cluster.get("source_record_ids", []))
        if signal.get("source_cluster_id") in {"needs_review", None}:
            return 46
        return cls._clip(52 + source_count * 6)

    @staticmethod
    def _status(total_score: float, risk_level: str, score_breakdown: dict[str, int]) -> str:
        if risk_level == "high":
            return "unsafe"
        if score_breakdown["evidence_confidence"] < 35 or score_breakdown["mobility_relevance"] < 25:
            return "noise"
        if total_score >= 72:
            return "high_value"
        if total_score >= 62:
            return "monitor"
        if total_score >= 45:
            return "low_value"
        return "noise"

    @staticmethod
    def _noise_reason(ranking_status: str, risk_level: str, score_breakdown: dict[str, int]) -> str:
        if ranking_status == "unsafe":
            return f"Risk level is {risk_level}; keep blocked and require explicit human review."
        if ranking_status == "noise":
            return "Evidence confidence or mobility relevance is too low to route into action."
        if ranking_status == "low_value":
            return "Signal has some relevance but insufficient score for immediate promotion planning."
        if ranking_status == "monitor":
            return "Signal is plausible but should wait for stronger evidence or human validation."
        return ""

    @staticmethod
    def _next_step(ranking_status: str) -> str:
        return {
            "high_value": "Send to human review for possible seasonal, spatial, or demand strategy analysis.",
            "monitor": "Keep in monitoring queue and wait for more evidence.",
            "low_value": "Archive as low-priority intelligence; do not generate action.",
            "noise": "Filter out from action queue and keep as audit evidence.",
            "unsafe": "Block from action and require human safety review before any downstream use.",
        }[ranking_status]

    @staticmethod
    def _summary(
        ranked: list[dict[str, Any]],
        high_value: list[dict[str, Any]],
        noise_filtered: list[dict[str, Any]],
        unsafe: list[dict[str, Any]],
    ) -> dict[str, Any]:
        status_counts: dict[str, int] = {}
        for item in ranked:
            status_counts[item["ranking_status"]] = status_counts.get(item["ranking_status"], 0) + 1
        return {
            "intelligence_ranking_ready": True,
            "ranked_count": len(ranked),
            "high_value_count": len(high_value),
            "monitor_count": status_counts.get("monitor", 0),
            "low_value_count": status_counts.get("low_value", 0),
            "noise_count": status_counts.get("noise", 0),
            "unsafe_count": len(unsafe),
            "status_counts": status_counts,
            "all_items_human_review_required": all(item["human_review_required"] for item in ranked),
            "auto_action_allowed": False,
            "auto_execute_allowed": False,
            "auto_publish_allowed": False,
            "auto_reply_allowed": False,
            "write_api_allowed": False,
            "unsafe_enters_action": False,
            "noise_enters_action": False,
            "next_recommendation": "Route only human-reviewed high-value intelligence into Seasonal Intelligence Engine; keep monitor, low-value, noise, and unsafe signals blocked.",
        }
