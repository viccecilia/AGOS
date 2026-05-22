"""Trend clustering for AGOS Scout Intelligence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.runtime_persistence import utc_now_iso
from services.topic_discovery_engine import TopicDiscoveryEngine


class TrendClusteringEngine:
    """Cluster discovered topics into cross-platform trend signals."""

    RAINY_DAY_CLUSTER: dict[str, Any] = {
        "cluster_id": "trend_cluster_tokyo_rainy_day",
        "cluster_name": "Tokyo rainy day travel friction",
        "canonical_pain_point": "Tokyo rainy day itinerary anxiety",
        "cluster_type": "cross_platform_trend",
        "platforms": ["Reddit", "TikTok", "YouTube", "Instagram"],
        "source_topics": ["Tokyo rain itinerary", "Tokyo indoor plan", "rain in Tokyo trip"],
        "similar_questions": [
            "What should I do in Tokyo when it rains all day?",
            "Tokyo rainy day itinerary for first-time visitors",
            "Is Shibuya still worth visiting during heavy rain?",
        ],
        "similar_trends": [
            "indoor Tokyo itinerary",
            "rain-safe food and shopping route",
            "first-time visitor weather anxiety",
        ],
        "emotion_tags": ["uncertainty", "planning anxiety", "weather frustration"],
        "max_emotion_score": 0.84,
        "frequency": 4,
        "cross_platform": True,
        "status": "clustered",
        "next_action": "Generate rain-safe Tokyo route strategy for JAG-LAB review.",
    }

    def __init__(self, root: str | Path = "runtime/trend_clusters") -> None:
        self.root = Path(root)
        self.report_path = self.root / "TREND_CLUSTERING_REPORT.json"
        self.clusters_path = self.root / "trend_clusters.json"
        self.sources_path = self.root / "trend_cluster_sources.json"

    def cluster(self, discovered_topics: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        source_report = TopicDiscoveryEngine().state()
        topics = discovered_topics or source_report.get("discoveredTopics", [])
        clusters = [self._cluster_from_topic(topic) for topic in topics]
        clusters.append(dict(self.RAINY_DAY_CLUSTER))
        clusters = self._dedupe_clusters(clusters)
        report = {
            "report_id": "TREND_CLUSTERING_REPORT",
            "created_at": utc_now_iso(),
            "status": "active",
            "scope": "local_only_no_external_platform_access",
            "clusterDimensions": [
                "similar_questions",
                "similar_trends",
                "cross_platform_discussion",
                "similar_emotion",
            ],
            "trendClusters": clusters,
            "clusterSummary": {
                "total_clusters": len(clusters),
                "cross_platform_clusters": len([item for item in clusters if item["cross_platform"]]),
                "high_emotion_clusters": len([item for item in clusters if item["max_emotion_score"] >= 0.78]),
                "top_clusters": [item["cluster_name"] for item in clusters[:3]],
            },
        }
        self.persist(report)
        return report

    def state(self) -> dict[str, Any]:
        if self.report_path.exists():
            return json.loads(self.report_path.read_text(encoding="utf-8"))
        return self.cluster()

    def persist(self, report: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.clusters_path.write_text(json.dumps(report["trendClusters"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.sources_path.write_text(
            json.dumps(
                {
                    "created_at": report["created_at"],
                    "clusterDimensions": report["clusterDimensions"],
                    "source": "TopicDiscoveryEngine.discoveredTopics plus local scout seed examples",
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )

    @staticmethod
    def _cluster_from_topic(topic: dict[str, Any]) -> dict[str, Any]:
        platforms = sorted(set(topic.get("platforms", [])))
        frequency = int(topic.get("frequency", 1))
        max_emotion = float(topic.get("max_emotion_score", 0.5))
        canonical = topic.get("canonical_pain_point", "Unknown trend")
        cross_platform = len(platforms) >= 2
        cluster_type = "cross_platform_trend" if cross_platform else "single_platform_signal"
        if topic.get("high_emotion"):
            cluster_type = "high_emotion_cluster" if not cross_platform else "cross_platform_high_emotion"
        return {
            "cluster_id": "trend_cluster_" + "".join(ch if ch.isalnum() else "_" for ch in canonical.lower()).strip("_"),
            "cluster_name": canonical,
            "canonical_pain_point": canonical,
            "cluster_type": cluster_type,
            "platforms": platforms,
            "source_topics": [canonical],
            "similar_questions": topic.get("sample_questions", []),
            "similar_trends": TrendClusteringEngine._similar_trends_for(canonical),
            "emotion_tags": TrendClusteringEngine._emotion_tags_for(canonical, max_emotion),
            "max_emotion_score": round(max_emotion, 3),
            "frequency": frequency,
            "cross_platform": cross_platform,
            "status": "clustered",
            "next_action": TrendClusteringEngine._next_action_for(canonical, cross_platform, max_emotion),
        }

    @staticmethod
    def _similar_trends_for(canonical: str) -> list[str]:
        lowered = canonical.lower()
        if "transport" in lowered or "station" in lowered:
            return ["station maze", "first-time transfer anxiety", "route confidence gap"]
        if "air fryer" in lowered:
            return ["grease cleanup", "post-cooking maintenance", "kitchen appliance frustration"]
        if "vacuum" in lowered:
            return ["lost suction", "cleaning performance doubt", "maintenance confusion"]
        return ["repeated question pattern", "emerging pain signal", "content opportunity"]

    @staticmethod
    def _emotion_tags_for(canonical: str, score: float) -> list[str]:
        tags = ["uncertainty"]
        lowered = canonical.lower()
        if score >= 0.78:
            tags.append("high_emotion")
        if "transport" in lowered or "station" in lowered:
            tags.append("travel anxiety")
        if "clean" in lowered or "vacuum" in lowered:
            tags.append("frustration")
        return tags

    @staticmethod
    def _next_action_for(canonical: str, cross_platform: bool, max_emotion: float) -> str:
        if cross_platform and max_emotion >= 0.78:
            return "Prioritize answer branch and short-form content strategy for human review."
        if max_emotion >= 0.78:
            return "Validate pain strength before generating a reply branch."
        return "Keep monitoring until repeated across more sources."

    @staticmethod
    def _dedupe_clusters(clusters: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen: set[str] = set()
        unique = []
        for cluster in sorted(clusters, key=lambda item: (item["cross_platform"], item["frequency"], item["max_emotion_score"]), reverse=True):
            if cluster["cluster_id"] in seen:
                continue
            seen.add(cluster["cluster_id"])
            unique.append(cluster)
        return unique


if __name__ == "__main__":
    result = TrendClusteringEngine().cluster()
    print(json.dumps({"status": result["status"], "clusters": len(result["trendClusters"])}, indent=2))
