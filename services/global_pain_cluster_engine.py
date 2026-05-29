"""Global pain cluster engine for read-only AGOS intelligence records."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from services.global_batch_intelligence_collection import GlobalBatchIntelligenceCollection
from services.runtime_persistence import utc_now_iso


DEFAULT_INPUT_PATH = Path("runtime/global_batch_intelligence_collection/global_intelligence_records.json")
DEFAULT_OUTPUT_DIR = Path("runtime/global_pain_clusters")

PAIN_METADATA = {
    "airport transfer confusion": {
        "cluster_name": "Airport transfer confusion",
        "pain_points": ["late arrival uncertainty", "airport pickup confusion", "luggage transfer stress"],
        "emotion_tags": ["anxious", "urgent", "overwhelmed"],
        "intent": "airport_transfer",
        "season": "peak arrival windows",
    },
    "family trip mobility stress": {
        "cluster_name": "Family trip mobility stress",
        "pain_points": ["kids and luggage burden", "multi-stop planning", "family comfort concern"],
        "emotion_tags": ["stressed", "careful", "risk_averse"],
        "intent": "family_trip",
        "season": "school holidays",
    },
    "event pickup demand": {
        "cluster_name": "Event pickup and exit demand",
        "pain_points": ["crowded venue exit", "wait time uncertainty", "post-event pickup difficulty"],
        "emotion_tags": ["impatient", "crowded", "time_sensitive"],
        "intent": "event_pickup",
        "season": "event calendar",
    },
    "public transport anxiety": {
        "cluster_name": "Public transport anxiety",
        "pain_points": ["confusing station transfers", "language friction", "first-trip uncertainty"],
        "emotion_tags": ["confused", "nervous", "lost"],
        "intent": "public_transport_anxiety",
        "season": "first-time visitor periods",
    },
    "seasonal crowd pressure": {
        "cluster_name": "Seasonal crowd pressure",
        "pain_points": ["crowd congestion", "hotel district pressure", "route uncertainty during peaks"],
        "emotion_tags": ["crowded", "worried", "planning_pressure"],
        "intent": "seasonal_private_transfer",
        "season": "seasonal peak",
    },
}


class GlobalPainClusterEngine:
    """Cluster global intelligence records into pain clusters without generating replies."""

    def __init__(
        self,
        input_path: str | Path = DEFAULT_INPUT_PATH,
        output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    ) -> None:
        self.input_path = Path(input_path)
        self.output_dir = Path(output_dir)
        self.report_path = self.output_dir / "GLOBAL_PAIN_CLUSTER_REPORT.json"
        self.clusters_path = self.output_dir / "global_pain_clusters.json"
        self.sources_path = self.output_dir / "pain_cluster_sources.json"
        self.feed_path = self.output_dir / "pain_cluster_feed.json"
        self.summary_path = self.output_dir / "global_pain_cluster_summary.json"

    def build(self, records: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        source_records = records if records is not None else self._load_records()
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for record in source_records:
            topic = self._cluster_topic(record)
            grouped[topic].append(record)

        clusters = [
            self._cluster(index, topic, items)
            for index, (topic, items) in enumerate(sorted(grouped.items()), start=1)
        ]
        clusters.sort(
            key=lambda item: (
                item["business_relevance_score"],
                item["emotion_intensity_score"],
                item["frequency_score"],
            ),
            reverse=True,
        )
        sources = self._sources(clusters)
        feed = self._feed(clusters)
        summary = self._summary(clusters, source_records)
        report = {
            "report_id": "GLOBAL_PAIN_CLUSTER_REPORT",
            "round_id": "ROUND-GLOBAL-002",
            "created_at": utc_now_iso(),
            "status": "global_pain_clusters_ready",
            "phase": "GLOBAL_INTELLIGENCE_COLLECTION",
            "input_path": str(self.input_path),
            "globalPainClusters": clusters,
            "painClusterSources": sources,
            "painClusterFeed": feed,
            "globalPainClusterSummary": summary,
            "safetyBoundary": "Global Pain Cluster Engine reads local/read-only global intelligence records only. It clusters pain points for analysis and does not generate replies, promote content, contact users, or call platform write APIs.",
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
        self.clusters_path.write_text(json.dumps(report["globalPainClusters"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.sources_path.write_text(json.dumps(report["painClusterSources"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.feed_path.write_text(json.dumps(report["painClusterFeed"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.summary_path.write_text(json.dumps(report["globalPainClusterSummary"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    def _load_records(self) -> list[dict[str, Any]]:
        if not self.input_path.exists():
            GlobalBatchIntelligenceCollection().collect()
        if not self.input_path.exists():
            return []
        payload = json.loads(self.input_path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, list) else []

    @staticmethod
    def _cluster_topic(record: dict[str, Any]) -> str:
        topic = str(record.get("topic") or record.get("keyword") or "uncategorized").strip().lower()
        return topic or "uncategorized"

    @staticmethod
    def _cluster(index: int, topic: str, records: list[dict[str, Any]]) -> dict[str, Any]:
        metadata = PAIN_METADATA.get(topic, {})
        markets = sorted({item.get("market", "unknown") for item in records})
        platforms = sorted({item.get("source_platform", item.get("platform", "unknown")) for item in records})
        languages = sorted({item.get("language", "unknown") for item in records})
        locations = sorted({item.get("region", "unknown") for item in records})
        source_ids = [item.get("record_id", "") for item in records if item.get("record_id")]
        frequency_score = min(100, 45 + len(records) * 8 + len(markets) * 4 + len(platforms) * 3)
        emotion_intensity_score = min(100, 50 + len(metadata.get("emotion_tags", [])) * 8 + len(records) * 3)
        business_relevance_score = min(100, 52 + len(metadata.get("pain_points", [])) * 8 + len(markets) * 3 + len(platforms) * 2)
        enter_ranking = business_relevance_score >= 75 or frequency_score >= 80
        return {
            "cluster_id": f"GLOBAL-PAIN-{index:03d}",
            "cluster_name": metadata.get("cluster_name", topic.title()),
            "cluster_key": topic,
            "markets": markets,
            "platforms": platforms,
            "languages": languages,
            "source_record_ids": source_ids,
            "pain_points": metadata.get("pain_points", [topic]),
            "emotion_tags": metadata.get("emotion_tags", ["needs_review"]),
            "intent": metadata.get("intent", "needs_classification"),
            "season": metadata.get("season", "unknown"),
            "locations": locations,
            "frequency_score": frequency_score,
            "emotion_intensity_score": emotion_intensity_score,
            "business_relevance_score": business_relevance_score,
            "cross_market": len(markets) > 1,
            "cross_platform": len(platforms) > 1,
            "enter_ranking": enter_ranking,
            "human_review_required": True,
            "auto_reply_allowed": False,
            "reply_generation_allowed": False,
            "promotion_allowed": False,
            "source_record_count": len(source_ids),
        }

    @staticmethod
    def _sources(clusters: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "cluster_id": cluster["cluster_id"],
                "cluster_name": cluster["cluster_name"],
                "source_record_ids": cluster["source_record_ids"],
                "source_record_count": cluster["source_record_count"],
                "markets": cluster["markets"],
                "platforms": cluster["platforms"],
                "human_review_required": cluster["human_review_required"],
            }
            for cluster in clusters
        ]

    @staticmethod
    def _feed(clusters: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "time": utc_now_iso(),
                "cluster_id": cluster["cluster_id"],
                "cluster_name": cluster["cluster_name"],
                "markets": cluster["markets"],
                "platforms": cluster["platforms"],
                "frequency_score": cluster["frequency_score"],
                "emotion_intensity_score": cluster["emotion_intensity_score"],
                "business_relevance_score": cluster["business_relevance_score"],
                "enter_ranking": cluster["enter_ranking"],
                "human_review_required": cluster["human_review_required"],
            }
            for cluster in clusters
        ]

    @staticmethod
    def _summary(clusters: list[dict[str, Any]], records: list[dict[str, Any]]) -> dict[str, Any]:
        market_counts = Counter(market for cluster in clusters for market in cluster["markets"])
        platform_counts = Counter(platform for cluster in clusters for platform in cluster["platforms"])
        high_emotion = [item for item in clusters if item["emotion_intensity_score"] >= 80]
        cross_market = [item for item in clusters if item["cross_market"]]
        cross_platform = [item for item in clusters if item["cross_platform"]]
        ranking_candidates = [item for item in clusters if item["enter_ranking"]]
        return {
            "global_pain_cluster_ready": True,
            "input_record_count": len(records),
            "cluster_count": len(clusters),
            "high_emotion_cluster_count": len(high_emotion),
            "cross_market_cluster_count": len(cross_market),
            "cross_platform_cluster_count": len(cross_platform),
            "ranking_candidate_count": len(ranking_candidates),
            "top_markets": dict(market_counts.most_common(8)),
            "top_platforms": dict(platform_counts.most_common(8)),
            "all_clusters_need_human_review": all(item["human_review_required"] for item in clusters),
            "auto_reply_allowed": False,
            "reply_generation_allowed": False,
            "promotion_allowed": False,
            "next_recommendation": "Send reviewed pain clusters into Intelligence Ranking and Noise Filtering after human review.",
        }


if __name__ == "__main__":
    result = GlobalPainClusterEngine().build()
    print(json.dumps({"status": result["status"], "summary": result["globalPainClusterSummary"]}, indent=2))
