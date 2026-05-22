"""Heat detection for AGOS Scout Intelligence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.runtime_persistence import utc_now_iso
from services.trend_clustering_engine import TrendClusteringEngine


class HeatDetectionEngine:
    """Detect hot trend signals and rank local growth opportunities."""

    def __init__(self, root: str | Path = "runtime/heat_signals") -> None:
        self.root = Path(root)
        self.report_path = self.root / "HEAT_DETECTION_REPORT.json"
        self.signals_path = self.root / "heat_signals.json"
        self.ranking_path = self.root / "opportunity_ranking.json"

    def detect(self, trend_clusters: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        source_report = TrendClusteringEngine().state()
        clusters = trend_clusters or source_report.get("trendClusters", [])
        heat_signals = [self._heat_signal_from_cluster(cluster) for cluster in clusters]
        opportunity_ranking = sorted(heat_signals, key=lambda item: item["opportunity_score"], reverse=True)
        for rank, signal in enumerate(opportunity_ranking, start=1):
            signal["rank"] = rank
        report = {
            "report_id": "HEAT_DETECTION_REPORT",
            "created_at": utc_now_iso(),
            "status": "active",
            "scope": "local_only_no_external_platform_access",
            "heatDimensions": [
                "rising_trend",
                "high_engagement_trend",
                "high_emotion_trend",
                "high_spread_trend",
            ],
            "heatSignals": heat_signals,
            "opportunityRanking": opportunity_ranking,
            "heatSummary": {
                "total_signals": len(heat_signals),
                "hot_signals": len([item for item in heat_signals if item["heat_level"] == "hot"]),
                "warming_signals": len([item for item in heat_signals if item["heat_level"] == "warming"]),
                "top_opportunity": opportunity_ranking[0]["cluster_name"] if opportunity_ranking else "none",
            },
        }
        self.persist(report)
        return report

    def state(self) -> dict[str, Any]:
        if self.report_path.exists():
            return json.loads(self.report_path.read_text(encoding="utf-8"))
        return self.detect()

    def persist(self, report: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.signals_path.write_text(json.dumps(report["heatSignals"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.ranking_path.write_text(json.dumps(report["opportunityRanking"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    @staticmethod
    def _heat_signal_from_cluster(cluster: dict[str, Any]) -> dict[str, Any]:
        frequency = int(cluster.get("frequency", 1))
        platform_count = len(set(cluster.get("platforms", [])))
        emotion_score = float(cluster.get("max_emotion_score", 0.5))
        cross_platform = bool(cluster.get("cross_platform"))

        rising_score = min(1.0, frequency / 5)
        engagement_score = min(1.0, (platform_count / 4) + (0.15 if cross_platform else 0))
        emotion_heat_score = min(1.0, emotion_score)
        spread_score = min(1.0, platform_count / 5 + (0.2 if cross_platform else 0))
        opportunity_score = round(
            rising_score * 0.25
            + engagement_score * 0.25
            + emotion_heat_score * 0.25
            + spread_score * 0.25,
            3,
        )
        heat_level = HeatDetectionEngine._heat_level(opportunity_score)
        return {
            "signal_id": "heat_" + cluster.get("cluster_id", "unknown").replace("trend_cluster_", ""),
            "cluster_id": cluster.get("cluster_id", "unknown"),
            "cluster_name": cluster.get("cluster_name", "Unknown trend"),
            "platforms": sorted(set(cluster.get("platforms", []))),
            "frequency": frequency,
            "rising_score": round(rising_score, 3),
            "engagement_score": round(engagement_score, 3),
            "emotion_heat_score": round(emotion_heat_score, 3),
            "spread_score": round(spread_score, 3),
            "opportunity_score": opportunity_score,
            "heat_level": heat_level,
            "detectedSignals": HeatDetectionEngine._detected_signals(rising_score, engagement_score, emotion_heat_score, spread_score),
            "why_hot": HeatDetectionEngine._why_hot(cluster, opportunity_score, platform_count),
            "recommended_action": HeatDetectionEngine._recommended_action(cluster, heat_level),
            "status": "detected",
        }

    @staticmethod
    def _heat_level(score: float) -> str:
        if score >= 0.78:
            return "hot"
        if score >= 0.62:
            return "warming"
        return "watch"

    @staticmethod
    def _detected_signals(rising: float, engagement: float, emotion: float, spread: float) -> list[str]:
        signals = []
        if rising >= 0.65:
            signals.append("rising_trend")
        if engagement >= 0.65:
            signals.append("high_engagement_trend")
        if emotion >= 0.78:
            signals.append("high_emotion_trend")
        if spread >= 0.65:
            signals.append("high_spread_trend")
        return signals or ["watch_signal"]

    @staticmethod
    def _why_hot(cluster: dict[str, Any], score: float, platform_count: int) -> str:
        return (
            f"{cluster.get('cluster_name', 'This trend')} scores {score} because it appears across "
            f"{platform_count} platform(s), has frequency {cluster.get('frequency', 1)}, "
            f"and emotion score {cluster.get('max_emotion_score', 0.5)}."
        )

    @staticmethod
    def _recommended_action(cluster: dict[str, Any], heat_level: str) -> str:
        if heat_level == "hot":
            return "Prioritize for human-reviewed answer branch and content strategy."
        if heat_level == "warming":
            return "Prepare draft strategy and monitor for another cycle."
        return "Keep in watchlist until stronger cross-platform evidence appears."


if __name__ == "__main__":
    result = HeatDetectionEngine().detect()
    print(json.dumps({"status": result["status"], "signals": len(result["heatSignals"])}, indent=2))
