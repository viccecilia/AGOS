"""Topic discovery for AGOS Scout Intelligence."""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from services.keyword_expansion_engine import KeywordExpansionEngine
from services.runtime_persistence import utc_now_iso


class TopicDiscoveryEngine:
    """Discover frequent, repeated, emerging, and high-emotion questions from local sources."""

    SAMPLE_ITEMS: list[dict[str, Any]] = [
        {
            "source_type": "rss",
            "source": "travel_rss_sample",
            "text": "Tokyo subway confusing for first time Japan trip. I am worried I will get lost.",
            "platform": "RSS",
            "emotion_score": 0.86,
            "created_at": "2026-05-22T01:00:00+00:00",
        },
        {
            "source_type": "manual_import",
            "source": "operator_note",
            "text": "东京地铁复杂，第一次去日本很怕换乘错。",
            "platform": "Manual",
            "emotion_score": 0.9,
            "created_at": "2026-05-22T02:00:00+00:00",
        },
        {
            "source_type": "json",
            "source": "imported_questions.json",
            "text": "Lost in station at Shinjuku, cannot find platform and panic.",
            "platform": "Reddit",
            "emotion_score": 0.88,
            "created_at": "2026-05-22T03:00:00+00:00",
        },
        {
            "source_type": "csv",
            "source": "questions.csv",
            "text": "Air fryer cleaning is frustrating, grease is everywhere.",
            "platform": "TikTok",
            "emotion_score": 0.78,
            "created_at": "2026-05-22T04:00:00+00:00",
        },
        {
            "source_type": "local_text",
            "source": "local_notes.txt",
            "text": "Vacuum lost suction and dust is still there after cleaning.",
            "platform": "YouTube",
            "emotion_score": 0.72,
            "created_at": "2026-05-22T05:00:00+00:00",
        },
        {
            "source_type": "manual_import",
            "source": "operator_note",
            "text": "Tokyo train transfer at Shinjuku is a station maze.",
            "platform": "Threads",
            "emotion_score": 0.81,
            "created_at": "2026-05-22T06:00:00+00:00",
        },
    ]

    def __init__(self, root: str | Path = "runtime/discovered_topics") -> None:
        self.root = Path(root)
        self.report_path = self.root / "DISCOVERED_TOPICS_REPORT.json"
        self.topics_path = self.root / "discovered_topics.json"
        self.sources_path = self.root / "topic_sources.json"
        self.keyword_engine = KeywordExpansionEngine()

    def discover(self, items: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        items = items or self.SAMPLE_ITEMS
        normalized_items = [self._normalize_item(item, index) for index, item in enumerate(items, start=1)]
        topics = self._group_topics(normalized_items)
        report = {
            "report_id": "DISCOVERED_TOPICS_REPORT",
            "created_at": utc_now_iso(),
            "status": "active",
            "supportedSources": ["RSS", "manual_import", "JSON", "CSV", "local_text"],
            "sourceItems": normalized_items,
            "discoveredTopics": topics,
            "topicSummary": {
                "total_source_items": len(normalized_items),
                "total_topics": len(topics),
                "high_emotion_topics": [topic["canonical_pain_point"] for topic in topics if topic["high_emotion"]],
                "frequent_topics": [topic["canonical_pain_point"] for topic in topics if topic["frequency"] >= 2],
                "emerging_topics": [topic["canonical_pain_point"] for topic in topics if topic["emerging"]],
            },
        }
        self.persist(report)
        return report

    def load_json_source(self, path: str | Path) -> list[dict[str, Any]]:
        return json.loads(Path(path).read_text(encoding="utf-8"))

    def load_csv_source(self, path: str | Path) -> list[dict[str, Any]]:
        with Path(path).open("r", encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    def load_text_source(self, path: str | Path) -> list[dict[str, Any]]:
        items = []
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            if line.strip():
                items.append({"source_type": "local_text", "source": str(path), "text": line.strip(), "emotion_score": 0.5})
        return items

    def state(self) -> dict[str, Any]:
        if self.report_path.exists():
            return json.loads(self.report_path.read_text(encoding="utf-8"))
        return self.discover()

    def persist(self, report: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.topics_path.write_text(json.dumps(report["discoveredTopics"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.sources_path.write_text(json.dumps(report["sourceItems"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    def _normalize_item(self, item: dict[str, Any], index: int) -> dict[str, Any]:
        text = str(item.get("text", ""))
        canonical = self._canonical_from_text(text)
        return {
            "item_id": item.get("item_id", f"topic_source_{index:03d}"),
            "source_type": item.get("source_type", "manual_import"),
            "source": item.get("source", "unknown"),
            "platform": item.get("platform", "Local"),
            "text": text,
            "canonical_pain_point": canonical,
            "emotion_score": float(item.get("emotion_score", 0.5)),
            "created_at": item.get("created_at", utc_now_iso()),
        }

    def _canonical_from_text(self, text: str) -> str:
        lowered = text.lower()
        expansion_state = self.keyword_engine.state()
        for expansion in expansion_state.get("keywordExpansions", []):
            candidates = [expansion["seed_keyword"], *expansion.get("expanded_terms", [])]
            if any(candidate.lower() in lowered or lowered in candidate.lower() for candidate in candidates):
                return expansion["canonical_pain_point"]
        return self.keyword_engine.normalize_phrase(text)

    @staticmethod
    def _group_topics(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for item in items:
            grouped[item["canonical_pain_point"]].append(item)
        source_counts = Counter(item["source_type"] for item in items)
        topics = []
        for canonical, topic_items in grouped.items():
            emotion_scores = [item["emotion_score"] for item in topic_items]
            frequency = len(topic_items)
            repeated = frequency >= 2
            high_emotion = max(emotion_scores) >= 0.78
            emerging = frequency == 1 and high_emotion or any(source_counts[item["source_type"]] == 1 for item in topic_items)
            topics.append(
                {
                    "topic_id": "topic_" + "".join(ch if ch.isalnum() else "_" for ch in canonical.lower()).strip("_"),
                    "canonical_pain_point": canonical,
                    "frequency": frequency,
                    "repeated": repeated,
                    "emerging": emerging,
                    "high_emotion": high_emotion,
                    "max_emotion_score": round(max(emotion_scores), 3),
                    "source_types": sorted({item["source_type"] for item in topic_items}),
                    "platforms": sorted({item["platform"] for item in topic_items}),
                    "sample_questions": [item["text"] for item in topic_items[:3]],
                    "status": "discovered",
                }
            )
        return sorted(topics, key=lambda topic: (topic["frequency"], topic["max_emotion_score"]), reverse=True)
