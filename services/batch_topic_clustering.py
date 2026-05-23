"""Batch topic clustering for high-value question groups."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from services.batch_scout_runtime import BatchScoutRuntime
from services.runtime_persistence import utc_now_iso


class BatchTopicClustering:
    """Cluster batch scout output into similar, frequent, emotional, and growth-signaled groups."""

    def __init__(self, root: str | Path = "runtime/batch_clusters") -> None:
        self.root = Path(root)
        self.report_path = self.root / "BATCH_TOPIC_CLUSTERING_REPORT.json"
        self.clusters_path = self.root / "batch_trend_clusters.json"
        self.feed_path = self.root / "batch_cluster_feed.json"
        self.summary_path = self.root / "batch_cluster_summary.json"

    def cluster(self, batch_analysis: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        analysis = batch_analysis
        if analysis is None:
            analysis = BatchScoutRuntime().state().get("batchAnalysis", [])
        clusters = [self._cluster_record(key, items) for key, items in self._group(analysis).items()]
        clusters = sorted(clusters, key=lambda item: item["growth_signal_score"], reverse=True)
        for rank, item in enumerate(clusters, start=1):
            item["rank"] = rank
        report = {
            "report_id": "BATCH_TOPIC_CLUSTERING_REPORT",
            "created_at": utc_now_iso(),
            "status": "batch_clusters_ready",
            "scope": "local_batch_topic_clustering",
            "clusterDimensions": [
                "similar_questions",
                "frequent_questions",
                "high_emotion_questions",
                "high_growth_signals",
            ],
            "batchTrendClusters": clusters,
            "batchClusterFeed": self._feed(clusters),
            "batchClusterSummary": self._summary(clusters, analysis),
            "safetyBoundary": "Batch Topic Clustering uses local batch analysis only. It does not post, reply, follow, DM, log in, register accounts, or call external write APIs.",
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
        self.clusters_path.write_text(json.dumps(report["batchTrendClusters"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.feed_path.write_text(json.dumps(report["batchClusterFeed"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.summary_path.write_text(json.dumps(report["batchClusterSummary"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    @staticmethod
    def _group(analysis: list[dict[str, Any]]) -> dict[tuple[str, str], list[dict[str, Any]]]:
        grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        for item in analysis:
            grouped[(item.get("class", "unknown"), item.get("detected_topic", "unknown"))].append(item)
        return grouped

    @staticmethod
    def _cluster_record(key: tuple[str, str], items: list[dict[str, Any]]) -> dict[str, Any]:
        category, topic = key
        frequency = len(items)
        avg_priority = round(sum(int(item.get("priority_score", 0)) for item in items) / max(frequency, 1), 2)
        high_emotion_items = [
            item for item in items if item.get("emotion") in {"anxiety", "frustration", "decision_pressure"}
        ]
        critical_items = [item for item in items if item.get("priority_band") == "critical"]
        platforms = sorted({item.get("platform", "unknown") for item in items})
        growth_signal_score = BatchTopicClustering._growth_score(frequency, avg_priority, len(high_emotion_items), len(platforms))
        return {
            "cluster_id": "batch_cluster_" + "".join(ch if ch.isalnum() else "_" for ch in f"{category}_{topic}".lower()).strip("_"),
            "cluster_name": topic,
            "category": category,
            "frequency": frequency,
            "platforms": platforms,
            "similar_question_count": frequency,
            "high_frequency": frequency >= 10,
            "high_emotion": len(high_emotion_items) >= max(3, frequency // 2),
            "high_growth_signal": growth_signal_score >= 80,
            "avg_priority_score": avg_priority,
            "critical_questions": len(critical_items),
            "growth_signal_score": growth_signal_score,
            "dominant_emotions": sorted({item.get("emotion", "unknown") for item in items}),
            "sample_questions": [item.get("question_text", "") for item in items[:5]],
            "source_question_ids": [item.get("question_id", "") for item in items],
            "recommended_cluster_action": BatchTopicClustering._recommended_action(category, topic, growth_signal_score),
            "status": "clustered",
        }

    @staticmethod
    def _growth_score(frequency: int, avg_priority: float, high_emotion_count: int, platform_count: int) -> int:
        frequency_score = min(frequency * 4, 40)
        priority_score = min(avg_priority * 0.35, 35)
        emotion_score = min(high_emotion_count * 3, 15)
        spread_score = min(platform_count * 2, 10)
        return min(round(frequency_score + priority_score + emotion_score + spread_score), 100)

    @staticmethod
    def _recommended_action(category: str, topic: str, score: int) -> str:
        if score >= 90:
            return f"Prioritize {topic} for batch answer branch generation and human-reviewed content planning."
        if category == "transport_confusion":
            return f"Create a transport confusion cluster pack for {topic}."
        if category == "payment_decision":
            return f"Create comparison answer branches for {topic}."
        if category == "weather_fallback":
            return f"Create contingency itinerary content for {topic}."
        return f"Keep clustering {topic} until stronger growth evidence appears."

    @staticmethod
    def _summary(clusters: list[dict[str, Any]], analysis: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "questions_clustered": len(analysis),
            "clusters_created": len(clusters),
            "high_frequency_clusters": len([item for item in clusters if item["high_frequency"]]),
            "high_emotion_clusters": len([item for item in clusters if item["high_emotion"]]),
            "high_growth_signal_clusters": len([item for item in clusters if item["high_growth_signal"]]),
            "top_cluster": clusters[0]["cluster_name"] if clusters else "none",
            "top_growth_signal_score": clusters[0]["growth_signal_score"] if clusters else 0,
            "batch_clustering_ready": bool(clusters),
        }

    @staticmethod
    def _feed(clusters: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "time": utc_now_iso(),
                "cluster_id": item["cluster_id"],
                "rank": item["rank"],
                "cluster_name": item["cluster_name"],
                "category": item["category"],
                "frequency": item["frequency"],
                "platforms": item["platforms"],
                "high_frequency": item["high_frequency"],
                "high_emotion": item["high_emotion"],
                "high_growth_signal": item["high_growth_signal"],
                "growth_signal_score": item["growth_signal_score"],
                "recommended_cluster_action": item["recommended_cluster_action"],
                "status": item["status"],
            }
            for item in clusters
        ]


if __name__ == "__main__":
    result = BatchTopicClustering().cluster()
    print(json.dumps({"status": result["status"], "clusters": result["batchClusterSummary"]["clusters_created"]}, indent=2))
