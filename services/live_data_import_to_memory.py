"""Import normalized live intelligence into AGOS training memory."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from services.heat_detection_engine import HeatDetectionEngine
from services.live_data_normalization_pipeline import LiveDataNormalizationPipeline
from services.runtime_pattern_learning import RuntimePatternLearning
from services.runtime_persistence import utc_now_iso
from services.runtime_replay_training import RuntimeReplayTraining


MEMORY_TARGETS = [
    "Question Inbox",
    "Pain Point Library",
    "Pattern Memory",
    "Trend Cluster",
    "Scout Intelligence",
]


class LiveDataImportToMemory:
    """Write live normalized intelligence into local memory stores and training triggers."""

    def __init__(self, root: str | Path = "runtime/live_memory_import") -> None:
        self.root = Path(root)
        self.report_path = self.root / "LIVE_DATA_IMPORT_TO_MEMORY_REPORT.json"
        self.question_inbox_path = self.root / "question_inbox_memory.json"
        self.pain_point_path = self.root / "pain_point_library_memory.json"
        self.pattern_path = self.root / "pattern_memory_import.json"
        self.trend_cluster_path = self.root / "trend_cluster_memory.json"
        self.scout_intelligence_path = self.root / "scout_intelligence_memory.json"
        self.feed_path = self.root / "memory_import_feed.json"
        self.summary_path = self.root / "memory_import_summary.json"

    def import_data(
        self,
        workspace_id: str = "JAG-LAB",
        normalized_items: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        items = normalized_items
        if items is None:
            items = LiveDataNormalizationPipeline().state().get("normalizedLiveData", [])

        question_inbox = [self._question_item(workspace_id, index, item) for index, item in enumerate(items, start=1)]
        pain_points = self._pain_point_memory(items)
        pattern_memory = [self._pattern_item(index, item) for index, item in enumerate(items, start=1)]
        trend_clusters = self._trend_clusters(items)
        scout_intelligence = [self._scout_item(index, item) for index, item in enumerate(items, start=1)]
        pattern_review_queue = self._pattern_review_queue(pattern_memory)

        triggered_pattern_learning = RuntimePatternLearning(self.root / "triggered_pattern_learning").learn(pattern_review_queue)
        triggered_replay_training = RuntimeReplayTraining(self.root / "triggered_replay_training").replay(
            {
                "questions": question_inbox,
                "reviews": pattern_review_queue,
                "patterns": triggered_pattern_learning.get("patternMemory", []),
                "replies": [],
                "feedback": [],
                "failures": [],
            }
        )
        triggered_ranking = HeatDetectionEngine(self.root / "triggered_intelligence_ranking").detect(trend_clusters)

        report = {
            "report_id": "LIVE_DATA_IMPORT_TO_MEMORY_REPORT",
            "created_at": utc_now_iso(),
            "status": "live_intelligence_imported_to_memory",
            "scope": "controlled_api_intelligence_collection",
            "workspace_id": workspace_id,
            "memoryTargets": MEMORY_TARGETS,
            "questionInboxMemory": question_inbox,
            "painPointLibraryMemory": pain_points,
            "patternMemoryImport": pattern_memory,
            "trendClusterMemory": trend_clusters,
            "scoutIntelligenceMemory": scout_intelligence,
            "triggeredPatternLearning": triggered_pattern_learning,
            "triggeredReplayTraining": triggered_replay_training,
            "triggeredIntelligenceRanking": triggered_ranking,
            "memoryImportFeed": self._feed(
                question_inbox,
                pain_points,
                pattern_memory,
                trend_clusters,
                scout_intelligence,
                triggered_pattern_learning,
                triggered_replay_training,
                triggered_ranking,
            ),
            "memoryImportSummary": self._summary(
                items,
                question_inbox,
                pain_points,
                pattern_memory,
                trend_clusters,
                scout_intelligence,
                triggered_pattern_learning,
                triggered_replay_training,
                triggered_ranking,
            ),
            "safetyBoundary": "Live Data Import to Memory writes local JSON training memory only. It does not post, reply, follow, DM, log in, register accounts, call platform write APIs, or bypass platform limits.",
        }
        self.persist(report)
        return report

    def state(self) -> dict[str, Any]:
        if self.report_path.exists():
            return json.loads(self.report_path.read_text(encoding="utf-8"))
        return self.import_data()

    def persist(self, report: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.question_inbox_path.write_text(json.dumps(report["questionInboxMemory"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.pain_point_path.write_text(json.dumps(report["painPointLibraryMemory"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.pattern_path.write_text(json.dumps(report["patternMemoryImport"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.trend_cluster_path.write_text(json.dumps(report["trendClusterMemory"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.scout_intelligence_path.write_text(json.dumps(report["scoutIntelligenceMemory"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.feed_path.write_text(json.dumps(report["memoryImportFeed"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.summary_path.write_text(json.dumps(report["memoryImportSummary"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    @staticmethod
    def _question_item(workspace_id: str, index: int, item: dict[str, Any]) -> dict[str, Any]:
        return {
            "question_id": f"LIVE-Q-{index:04d}",
            "workspace_id": workspace_id,
            "platform": item.get("platform", "unknown"),
            "language": item.get("language", "unknown"),
            "market": item.get("market", "global"),
            "source_url": item.get("source_url", ""),
            "question_text": item.get("normalized_text") or item.get("topic") or item.get("keyword") or "live intelligence signal",
            "pain_points": item.get("pain_points", []),
            "emotion_tags": item.get("emotion_tags", []),
            "status": "new",
            "priority_score": item.get("training_value_score", 0),
            "source_normalized_id": item.get("normalized_id", ""),
            "created_at": utc_now_iso(),
        }

    @staticmethod
    def _pain_point_memory(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        seen: set[tuple[str, str, str]] = set()
        for item in items:
            for pain_point in item.get("pain_points", []) or ["general_information_need"]:
                key = (pain_point, item.get("platform", "unknown"), item.get("market", "global"))
                if key in seen:
                    continue
                seen.add(key)
                records.append(
                    {
                        "pain_point_id": f"LIVE-PAIN-{len(records) + 1:04d}",
                        "pain_point": pain_point,
                        "platform": item.get("platform", "unknown"),
                        "market": item.get("market", "global"),
                        "emotion_tags": item.get("emotion_tags", []),
                        "trend_strength": item.get("trend_strength", 0),
                        "training_value_score": item.get("training_value_score", 0),
                        "source_confidence": item.get("source_confidence", 0),
                        "source_normalized_id": item.get("normalized_id", ""),
                        "created_at": utc_now_iso(),
                    }
                )
        return records

    @staticmethod
    def _pattern_item(index: int, item: dict[str, Any]) -> dict[str, Any]:
        score = int(item.get("training_value_score", 0))
        pattern_type = "high_value" if score >= 85 else "high_engagement" if score >= 70 else "watch_signal"
        pain_points = item.get("pain_points", []) or ["general_information_need"]
        return {
            "pattern_id": f"LIVE-PATTERN-{index:04d}",
            "source_normalized_id": item.get("normalized_id", ""),
            "pattern_type": pattern_type,
            "question_combination": f"{item.get('platform', 'unknown')} + {'/'.join(pain_points)} + {item.get('market', 'global')}",
            "result_pattern": f"{pain_points[0]} is a live intelligence pattern with training value {score}.",
            "learning_weight": round(min(1.0, 0.45 + score / 150), 2),
            "recommended_next_action": "Route into answer strategy and human-reviewed training memory.",
            "created_at": utc_now_iso(),
        }

    @staticmethod
    def _trend_clusters(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for item in items:
            pain_point = (item.get("pain_points") or ["general_information_need"])[0]
            grouped[pain_point].append(item)

        clusters = []
        for index, (pain_point, cluster_items) in enumerate(sorted(grouped.items()), start=1):
            platforms = sorted({item.get("platform", "unknown") for item in cluster_items})
            max_score = max((int(item.get("training_value_score", 0)) for item in cluster_items), default=0)
            clusters.append(
                {
                    "cluster_id": f"LIVE-CLUSTER-{index:04d}",
                    "cluster_name": pain_point.replace("_", " ").title(),
                    "canonical_pain_point": pain_point,
                    "platforms": platforms,
                    "source_items": [item.get("normalized_id", "") for item in cluster_items],
                    "emotion_tags": sorted({tag for item in cluster_items for tag in item.get("emotion_tags", [])}),
                    "frequency": len(cluster_items),
                    "max_trend_strength": max((int(item.get("trend_strength", 0)) for item in cluster_items), default=0),
                    "max_emotion_score": round(max_score / 100, 2),
                    "cross_platform": len(platforms) > 1,
                    "status": "clustered_from_live_data",
                    "created_at": utc_now_iso(),
                }
            )
        return clusters

    @staticmethod
    def _scout_item(index: int, item: dict[str, Any]) -> dict[str, Any]:
        pain_points = item.get("pain_points", []) or ["general_information_need"]
        return {
            "scout_id": f"LIVE-SCOUT-{index:04d}",
            "platform": item.get("platform", "unknown"),
            "source_type": item.get("source_type", "platform_signal"),
            "source_url": item.get("source_url", ""),
            "market": item.get("market", "global"),
            "language": item.get("language", "unknown"),
            "signal": item.get("normalized_text") or item.get("topic") or pain_points[0],
            "why_important": f"{pain_points[0]} has training value {item.get('training_value_score', 0)} and source confidence {item.get('source_confidence', 0)}.",
            "training_value_score": item.get("training_value_score", 0),
            "source_confidence": item.get("source_confidence", 0),
            "next_action": "Import into local training memory and keep write actions blocked.",
            "created_at": utc_now_iso(),
        }

    @staticmethod
    def _pattern_review_queue(pattern_memory: list[dict[str, Any]]) -> list[dict[str, Any]]:
        review_queue = []
        for index, pattern in enumerate(pattern_memory, start=1):
            review_queue.append(
                {
                    "review_id": f"LIVE-MEM-REVIEW-{index:04d}",
                    "cluster_id": pattern["pattern_id"],
                    "cluster_name": pattern["question_combination"],
                    "category": "live_memory_import",
                    "question_count": 1,
                    "decision": "classify",
                    "label": "high_value" if pattern["pattern_type"] == "high_value" else "watch",
                    "risk_flag": "low",
                }
            )
        return review_queue

    @staticmethod
    def _feed(
        question_inbox: list[dict[str, Any]],
        pain_points: list[dict[str, Any]],
        pattern_memory: list[dict[str, Any]],
        trend_clusters: list[dict[str, Any]],
        scout_intelligence: list[dict[str, Any]],
        pattern_learning: dict[str, Any],
        replay_training: dict[str, Any],
        ranking: dict[str, Any],
    ) -> list[dict[str, Any]]:
        return [
            {
                "time": utc_now_iso(),
                "target": "Question Inbox",
                "imported": len(question_inbox),
                "result": "live questions ready for review",
                "trigger": "Replay Training",
                "triggered": replay_training.get("replayTrainingSummary", {}).get("replay_training_ready", False),
            },
            {
                "time": utc_now_iso(),
                "target": "Pain Point Library",
                "imported": len(pain_points),
                "result": "live pain points mapped",
                "trigger": "Pattern Learning",
                "triggered": pattern_learning.get("patternLearningSummary", {}).get("pattern_memory_ready", False),
            },
            {
                "time": utc_now_iso(),
                "target": "Pattern Memory",
                "imported": len(pattern_memory),
                "result": "question-result patterns prepared",
                "trigger": "Pattern Learning",
                "triggered": pattern_learning.get("patternLearningSummary", {}).get("pattern_memory_ready", False),
            },
            {
                "time": utc_now_iso(),
                "target": "Trend Cluster",
                "imported": len(trend_clusters),
                "result": "live signals clustered",
                "trigger": "Intelligence Ranking",
                "triggered": bool(ranking.get("opportunityRanking", [])),
            },
            {
                "time": utc_now_iso(),
                "target": "Scout Intelligence",
                "imported": len(scout_intelligence),
                "result": "scout memory updated",
                "trigger": "Intelligence Ranking",
                "triggered": bool(ranking.get("opportunityRanking", [])),
            },
        ]

    @staticmethod
    def _summary(
        normalized_items: list[dict[str, Any]],
        question_inbox: list[dict[str, Any]],
        pain_points: list[dict[str, Any]],
        pattern_memory: list[dict[str, Any]],
        trend_clusters: list[dict[str, Any]],
        scout_intelligence: list[dict[str, Any]],
        pattern_learning: dict[str, Any],
        replay_training: dict[str, Any],
        ranking: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "import_ready": bool(normalized_items),
            "normalized_items_imported": len(normalized_items),
            "question_inbox_items": len(question_inbox),
            "pain_points_imported": len(pain_points),
            "patterns_imported": len(pattern_memory),
            "trend_clusters_imported": len(trend_clusters),
            "scout_intelligence_items": len(scout_intelligence),
            "replay_training_triggered": replay_training.get("replayTrainingSummary", {}).get("replay_training_ready", False),
            "pattern_learning_triggered": pattern_learning.get("patternLearningSummary", {}).get("pattern_memory_ready", False),
            "intelligence_ranking_triggered": bool(ranking.get("opportunityRanking", [])),
            "top_memory_target": "Question Inbox" if question_inbox else "none",
            "write_operations_enabled": False,
        }


if __name__ == "__main__":
    result = LiveDataImportToMemory().import_data()
    print(json.dumps({"status": result["status"], "summary": result["memoryImportSummary"]}, indent=2))
