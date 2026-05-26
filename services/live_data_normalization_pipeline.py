"""Normalize live collection intelligence into the AGOS training data model."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.live_collection_runner import LiveCollectionRunner
from services.runtime_persistence import utc_now_iso


PLATFORM_SOURCE_TYPES = {
    "TikTok": "TikTok trend",
    "Reddit": "Reddit topic",
    "YouTube": "YouTube search",
    "X": "X signal",
}

PAIN_POINT_RULES = {
    "transport": "transport_confusion",
    "subway": "transport_confusion",
    "pass": "payment_and_pass_decision",
    "ic card": "payment_and_pass_decision",
    "jr pass": "payment_and_pass_decision",
    "airport": "airport_transfer_confusion",
    "mistakes": "first_trip_uncertainty",
    "worth": "value_decision_pressure",
}

EMOTION_RULES = {
    "anxiety": "anxiety",
    "confusing": "anxiety",
    "confusion": "anxiety",
    "mistakes": "frustration",
    "debate": "comparison_pressure",
    "worth": "decision_pressure",
    "react": "surprise",
    "asking": "information_need",
}


class LiveDataNormalizationPipeline:
    """Convert platform-specific live collection items into one AGOS data shape."""

    def __init__(self, root: str | Path = "runtime/normalized_live_data") -> None:
        self.root = Path(root)
        self.report_path = self.root / "LIVE_DATA_NORMALIZATION_REPORT.json"
        self.items_path = self.root / "normalized_live_data.json"
        self.feed_path = self.root / "normalized_live_data_feed.json"
        self.summary_path = self.root / "normalization_summary.json"

    def normalize(self, live_items: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        source_items = live_items
        if source_items is None:
            source_items = LiveCollectionRunner().state().get("liveCollectionItems", [])
        normalized = [self._normalize_item(index, item) for index, item in enumerate(source_items, start=1)]
        report = {
            "report_id": "LIVE_DATA_NORMALIZATION_REPORT",
            "created_at": utc_now_iso(),
            "status": "live_data_normalized",
            "scope": "controlled_api_intelligence_collection",
            "requiredFields": [
                "platform",
                "source_url",
                "language",
                "market",
                "pain_points",
                "emotion_tags",
                "trend_strength",
                "training_value_score",
                "source_confidence",
            ],
            "normalizedLiveData": normalized,
            "normalizedLiveDataFeed": self._feed(normalized),
            "liveDataNormalizationSummary": self._summary(normalized),
            "safetyBoundary": "Live Data Normalization Pipeline reads local live collection data and writes local JSON only. It does not call platform APIs, post, reply, DM, follow, like, log in, or bypass platform limits.",
        }
        self.persist(report)
        return report

    def state(self) -> dict[str, Any]:
        if self.report_path.exists():
            return json.loads(self.report_path.read_text(encoding="utf-8"))
        return self.normalize()

    def persist(self, report: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.items_path.write_text(json.dumps(report["normalizedLiveData"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.feed_path.write_text(json.dumps(report["normalizedLiveDataFeed"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.summary_path.write_text(json.dumps(report["liveDataNormalizationSummary"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    def _normalize_item(self, index: int, item: dict[str, Any]) -> dict[str, Any]:
        platform = item.get("platform", "unknown")
        text = self._text(item)
        pain_points = self._pain_points(text)
        emotion_tags = self._emotion_tags(text)
        trend_strength = int(item.get("collection_score", 0))
        confidence = self._source_confidence(item)
        training_value = self._training_value_score(trend_strength, pain_points, emotion_tags, confidence)
        return {
            "normalized_id": f"LIVE-NORM-{index:04d}",
            "source_collection_id": item.get("collection_id", f"LIVE-COLLECT-{index:04d}"),
            "source_type": PLATFORM_SOURCE_TYPES.get(platform, "platform_signal"),
            "platform": platform,
            "source_url": item.get("source_url") or f"local://live_collection/{item.get('collection_id', f'LIVE-COLLECT-{index:04d}')}",
            "language": self._language(text),
            "market": self._market(text),
            "pain_points": pain_points,
            "emotion_tags": emotion_tags,
            "trend_strength": trend_strength,
            "training_value_score": training_value,
            "source_confidence": confidence,
            "topic": item.get("query", ""),
            "keyword": item.get("keyword", ""),
            "hashtag": item.get("hashtag", ""),
            "normalized_text": item.get("public_signal_text", ""),
            "read_status": item.get("read_status", "collected"),
            "write_status": "blocked",
            "human_review_required": True,
            "normalized_at": utc_now_iso(),
            "why_normalized": f"{platform} live signal mapped into shared AGOS platform/source/language/market/pain/emotion/strength/training/confidence fields.",
        }

    @staticmethod
    def _text(item: dict[str, Any]) -> str:
        return " ".join(
            str(item.get(key, ""))
            for key in ("query", "keyword", "hashtag", "public_signal_text")
        )

    @staticmethod
    def _language(text: str) -> str:
        # Current sample live collection inputs are English public signals.
        if any(ord(ch) > 127 for ch in text):
            return "mixed"
        return "en" if text.strip() else "unknown"

    @staticmethod
    def _market(text: str) -> str:
        lowered = text.lower()
        if "tokyo" in lowered or "japan" in lowered or "jr pass" in lowered or "suica" in lowered or "pasmo" in lowered:
            return "Japan"
        return "global"

    @staticmethod
    def _pain_points(text: str) -> list[str]:
        lowered = text.lower()
        points = [label for hint, label in PAIN_POINT_RULES.items() if hint in lowered]
        return sorted(set(points)) or ["general_information_need"]

    @staticmethod
    def _emotion_tags(text: str) -> list[str]:
        lowered = text.lower()
        tags = [label for hint, label in EMOTION_RULES.items() if hint in lowered]
        return sorted(set(tags)) or ["neutral_information_need"]

    @staticmethod
    def _source_confidence(item: dict[str, Any]) -> float:
        metric = item.get("public_metric", {})
        mentions = int(metric.get("mentions", 0))
        comments = int(metric.get("comments", 0))
        score = int(metric.get("score", 0))
        confidence = 0.45 + min(mentions, 60) * 0.003 + min(comments, 30) * 0.006 + min(score, 100) * 0.002
        if item.get("read_status") == "collected" and item.get("write_status") == "blocked":
            confidence += 0.05
        return round(min(confidence, 0.95), 3)

    @staticmethod
    def _training_value_score(
        trend_strength: int,
        pain_points: list[str],
        emotion_tags: list[str],
        source_confidence: float,
    ) -> int:
        score = trend_strength * 0.55 + len(pain_points) * 8 + len(emotion_tags) * 6 + source_confidence * 20
        return min(round(score), 100)

    @staticmethod
    def _feed(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "time": item["normalized_at"],
                "normalized_id": item["normalized_id"],
                "platform": item["platform"],
                "source_type": item["source_type"],
                "language": item["language"],
                "market": item["market"],
                "pain_points": item["pain_points"],
                "emotion_tags": item["emotion_tags"],
                "trend_strength": item["trend_strength"],
                "training_value_score": item["training_value_score"],
                "source_confidence": item["source_confidence"],
                "source_url": item["source_url"],
            }
            for item in items
        ]

    @staticmethod
    def _summary(items: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "pipeline_ready": True,
            "items_normalized": len(items),
            "platforms": sorted({item["platform"] for item in items}),
            "languages": sorted({item["language"] for item in items}),
            "markets": sorted({item["market"] for item in items}),
            "pain_points": sorted({pain for item in items for pain in item["pain_points"]}),
            "emotion_tags": sorted({emotion for item in items for emotion in item["emotion_tags"]}),
            "highest_training_value": max((item["training_value_score"] for item in items), default=0),
            "average_source_confidence": round(sum(item["source_confidence"] for item in items) / len(items), 3) if items else 0,
            "write_operations_enabled": False,
        }


if __name__ == "__main__":
    result = LiveDataNormalizationPipeline().normalize()
    print(json.dumps({"status": result["status"], "items": result["liveDataNormalizationSummary"]["items_normalized"]}, indent=2))
