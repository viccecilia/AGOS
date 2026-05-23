"""Bridge normalized API signals into the AGOS Scout Intelligence pipeline."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.api_signal_normalization import APISignalNormalization
from services.heat_detection_engine import HeatDetectionEngine
from services.keyword_expansion_engine import KeywordExpansionEngine
from services.patrol_group_engine import PatrolGroupEngine
from services.runtime_persistence import utc_now_iso
from services.strategic_interpretation_engine import StrategicInterpretationEngine
from services.topic_discovery_engine import TopicDiscoveryEngine
from services.trend_clustering_engine import TrendClusteringEngine


class APIToScoutPipeline:
    """Move read-only API trend signals through the Scout Intelligence chain."""

    def __init__(self, root: str | Path = "runtime/api_scout_pipeline") -> None:
        self.root = Path(root)
        self.report_path = self.root / "API_TO_SCOUT_PIPELINE_REPORT.json"
        self.feed_path = self.root / "api_scout_feed.json"
        self.trace_path = self.root / "api_scout_trace.json"

    def run(self, normalized_signals: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        api_report = APISignalNormalization().state()
        signals = normalized_signals if normalized_signals is not None else api_report.get("normalizedSignals", [])

        patrol_state = PatrolGroupEngine().build_all()
        keyword_state = KeywordExpansionEngine().build_from_patrol_groups()
        topic_items = [self._signal_to_topic_item(signal, index) for index, signal in enumerate(signals, start=1)]
        topic_report = TopicDiscoveryEngine().discover(topic_items)
        cluster_report = TrendClusteringEngine().cluster(topic_report.get("discoveredTopics", []))
        heat_report = HeatDetectionEngine().detect(cluster_report.get("trendClusters", []))
        strategic_report = StrategicInterpretationEngine().interpret(heat_report.get("opportunityRanking", []))

        trace = self._trace(
            signals=signals,
            patrol_state=patrol_state,
            keyword_state=keyword_state,
            topic_report=topic_report,
            cluster_report=cluster_report,
            heat_report=heat_report,
            strategic_report=strategic_report,
        )
        feed = self._feed(trace)
        report = {
            "report_id": "API_TO_SCOUT_PIPELINE_REPORT",
            "created_at": utc_now_iso(),
            "status": "api_trends_entered_scout_intelligence",
            "scope": "read_only_api_to_scout_pipeline",
            "pipelineStages": [
                "API Signal Normalization",
                "Patrol Groups",
                "Keyword Expansion",
                "Topic Discovery",
                "Trend Clustering",
                "Heat Detection",
                "Strategic Interpretation",
            ],
            "sourceSignals": signals,
            "topicItems": topic_items,
            "apiScoutTrace": trace,
            "apiScoutFeed": feed,
            "apiScoutPipelineSummary": {
                "source_signals": len(signals),
                "patrol_groups": len(patrol_state.get("activePatrolGroups", [])),
                "keyword_expansions": len(keyword_state.get("keywordExpansions", [])),
                "discovered_topics": len(topic_report.get("discoveredTopics", [])),
                "trend_clusters": len(cluster_report.get("trendClusters", [])),
                "heat_signals": len(heat_report.get("heatSignals", [])),
                "strategic_interpretations": len(strategic_report.get("strategicInterpretations", [])),
                "api_trends_entered_scout": bool(signals and topic_report.get("discoveredTopics")),
                "write_operations_enabled": False,
            },
            "safetyBoundary": "Pipeline consumes read-only API signals and writes local Scout Intelligence JSON only. It does not post, reply, follow, DM, scrape login-only pages, or bypass platform limits.",
        }
        self.persist(report)
        return report

    def state(self) -> dict[str, Any]:
        if self.report_path.exists():
            return json.loads(self.report_path.read_text(encoding="utf-8"))
        return self.run()

    def persist(self, report: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.feed_path.write_text(json.dumps(report["apiScoutFeed"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.trace_path.write_text(json.dumps(report["apiScoutTrace"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    @staticmethod
    def _signal_to_topic_item(signal: dict[str, Any], index: int) -> dict[str, Any]:
        strength = int(signal.get("trend_strength", 50))
        emotion_score = min(0.99, max(0.5, strength / 100))
        text_parts = [
            signal.get("topic", ""),
            signal.get("keyword", ""),
            signal.get("hashtag", ""),
            signal.get("normalized_text", ""),
            signal.get("emotion", ""),
        ]
        return {
            "item_id": f"api_topic_source_{index:03d}",
            "source_type": "read_only_api_signal",
            "source": signal.get("source_signal_type", "api_signal"),
            "platform": signal.get("platform", "unknown"),
            "text": " ".join(part for part in text_parts if part).strip(),
            "emotion_score": round(emotion_score, 3),
            "created_at": signal.get("normalized_at", utc_now_iso()),
        }

    @staticmethod
    def _trace(
        *,
        signals: list[dict[str, Any]],
        patrol_state: dict[str, Any],
        keyword_state: dict[str, Any],
        topic_report: dict[str, Any],
        cluster_report: dict[str, Any],
        heat_report: dict[str, Any],
        strategic_report: dict[str, Any],
    ) -> list[dict[str, Any]]:
        return [
            {
                "stage": "API Signal Normalization",
                "status": "completed",
                "items": len(signals),
                "evidence": [item.get("signal_id", "") for item in signals],
                "result": "Normalized read-only platform API trends are ready for Scout Intelligence.",
            },
            {
                "stage": "Patrol Groups",
                "status": patrol_state.get("status", "active"),
                "items": len(patrol_state.get("activePatrolGroups", [])),
                "evidence": patrol_state.get("supportedPlatforms", []),
                "result": "Workspace and industry-pack patrol groups provide platform context.",
            },
            {
                "stage": "Keyword Expansion",
                "status": keyword_state.get("status", "active"),
                "items": len(keyword_state.get("keywordExpansions", [])),
                "evidence": keyword_state.get("canonicalPainPoints", []),
                "result": "API topics are mapped against canonical pain-point language.",
            },
            {
                "stage": "Topic Discovery",
                "status": topic_report.get("status", "active"),
                "items": len(topic_report.get("discoveredTopics", [])),
                "evidence": [item.get("canonical_pain_point", "") for item in topic_report.get("discoveredTopics", [])],
                "result": "API trends entered discovered Scout topics.",
            },
            {
                "stage": "Trend Clustering",
                "status": cluster_report.get("status", "active"),
                "items": len(cluster_report.get("trendClusters", [])),
                "evidence": [item.get("cluster_name", "") for item in cluster_report.get("trendClusters", [])],
                "result": "Discovered API topics are grouped into trend clusters.",
            },
            {
                "stage": "Heat Detection",
                "status": heat_report.get("status", "active"),
                "items": len(heat_report.get("heatSignals", [])),
                "evidence": [item.get("cluster_name", "") for item in heat_report.get("opportunityRanking", [])],
                "result": "Trend clusters are scored and ranked as opportunities.",
            },
            {
                "stage": "Strategic Interpretation",
                "status": strategic_report.get("status", "active"),
                "items": len(strategic_report.get("strategicInterpretations", [])),
                "evidence": [item.get("cluster_name", "") for item in strategic_report.get("strategicInterpretations", [])],
                "result": "Scout Intelligence explains why API trends matter and what to do next.",
            },
        ]

    @staticmethod
    def _feed(trace: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "time": utc_now_iso(),
                "stage": item["stage"],
                "status": item["status"],
                "items": item["items"],
                "result": item["result"],
                "evidence": item["evidence"][:4],
            }
            for item in trace
        ]


if __name__ == "__main__":
    result = APIToScoutPipeline().run()
    print(json.dumps({"status": result["status"], "stages": len(result["pipelineStages"])}, indent=2))
