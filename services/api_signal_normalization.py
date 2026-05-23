"""Normalize read-only platform trend signals into one AGOS signal model."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.read_only_trend_connector import ReadOnlyTrendConnector
from services.runtime_persistence import utc_now_iso


PLATFORM_SIGNAL_TYPES = {
    "TikTok": "tiktok_trends",
    "Reddit": "reddit_hot_topics",
    "YouTube": "youtube_search",
    "X": "x_trend_data",
}

LANGUAGE_HINTS = {
    "Tokyo": "en",
    "Japan": "en",
    "IC card": "en",
    "JR Pass": "en",
    "东京": "zh",
    "地铁": "zh",
    "日本": "zh",
}

EMOTION_RULES = {
    "confusing": "anxiety",
    "confusion": "anxiety",
    "anxiety": "anxiety",
    "mistakes": "frustration",
    "debate": "comparison_pressure",
    "worth": "decision_pressure",
    "compare": "decision_pressure",
    "复杂": "anxiety",
}


class APISignalNormalization:
    """Unify platform-specific trend records into comparable growth signals."""

    def __init__(self, root: str | Path = "runtime/api_normalized_signals") -> None:
        self.root = Path(root)
        self.report_path = self.root / "API_SIGNAL_NORMALIZATION_REPORT.json"
        self.signals_path = self.root / "normalized_signals.json"
        self.feed_path = self.root / "api_normalized_signal_feed.json"

    def normalize(self, platform_trends: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        trends = platform_trends
        if trends is None:
            trends = ReadOnlyTrendConnector().state().get("platformTrends", [])
        normalized = [self._normalize_item(index, item) for index, item in enumerate(trends, start=1)]
        report = {
            "report_id": "API_SIGNAL_NORMALIZATION_REPORT",
            "created_at": utc_now_iso(),
            "status": "signals_normalized",
            "scope": "read_only_api_signal_normalization",
            "supportedSignalTypes": sorted(set(PLATFORM_SIGNAL_TYPES.values())),
            "normalizedSignals": normalized,
            "apiNormalizedSignalFeed": self._feed(normalized),
            "normalizationSummary": {
                "signals_normalized": len(normalized),
                "platforms": len({item["platform"] for item in normalized}),
                "languages": sorted({item["language"] for item in normalized}),
                "emotion_tags": sorted({item["emotion"] for item in normalized}),
                "highest_strength_signal": max(normalized, key=lambda item: item["trend_strength"])["signal_id"] if normalized else "none",
                "write_operations_enabled": False,
            },
            "safetyBoundary": "Normalizer reads existing trend signals and writes local JSON only. It does not call platform APIs, post, reply, follow, DM, or trigger engagement.",
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
        self.signals_path.write_text(json.dumps(report["normalizedSignals"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.feed_path.write_text(json.dumps(report["apiNormalizedSignalFeed"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    def _normalize_item(self, index: int, item: dict[str, Any]) -> dict[str, Any]:
        text = " ".join(
            [
                str(item.get("query", "")),
                str(item.get("keyword", "")),
                str(item.get("hashtag", "")),
                str(item.get("trend_text", "")),
            ]
        )
        platform = item.get("platform", "unknown")
        heat_score = int(item.get("heat_score", 0))
        metric = item.get("public_metric", {})
        comments = int(metric.get("comments", 0))
        mentions = int(metric.get("mentions", 0))
        return {
            "signal_id": f"API-SIGNAL-{index:04d}",
            "source_trend_id": item.get("trend_id", f"TREND-{index:04d}"),
            "source_signal_type": PLATFORM_SIGNAL_TYPES.get(platform, "generic_platform_trend"),
            "platform": platform,
            "language": self._language(text),
            "market": self._market(text),
            "emotion": self._emotion(text),
            "topic": item.get("query", ""),
            "keyword": item.get("keyword", ""),
            "hashtag": item.get("hashtag", ""),
            "normalized_text": item.get("trend_text", ""),
            "trend_strength": self._trend_strength(heat_score, mentions, comments),
            "engagement_potential": self._engagement_potential(platform, heat_score, comments),
            "content_potential": self._content_potential(platform, text),
            "reply_potential": self._reply_potential(platform, text),
            "read_status": item.get("read_status", "read"),
            "write_status": "blocked",
            "human_review_required": True,
            "normalized_at": utc_now_iso(),
            "why_unified": f"{platform} signal mapped into shared language/emotion/strength/potential fields.",
        }

    @staticmethod
    def _language(text: str) -> str:
        for hint, language in LANGUAGE_HINTS.items():
            if hint.lower() in text.lower():
                return language
        return "unknown"

    @staticmethod
    def _market(text: str) -> str:
        lowered = text.lower()
        if "tokyo" in lowered or "japan" in lowered or "jr pass" in lowered or "日本" in text or "东京" in text:
            return "Japan"
        return "global"

    @staticmethod
    def _emotion(text: str) -> str:
        lowered = text.lower()
        for hint, emotion in EMOTION_RULES.items():
            if hint.lower() in lowered:
                return emotion
        return "information_need"

    @staticmethod
    def _trend_strength(heat_score: int, mentions: int, comments: int) -> int:
        return min(round(heat_score * 0.7 + mentions * 0.2 + comments * 0.4), 100)

    @staticmethod
    def _engagement_potential(platform: str, heat_score: int, comments: int) -> str:
        score = heat_score + comments
        if platform in {"Reddit", "TikTok"}:
            score += 8
        if score >= 100:
            return "high"
        if score >= 70:
            return "medium"
        return "low"

    @staticmethod
    def _content_potential(platform: str, text: str) -> str:
        lowered = text.lower()
        if platform in {"TikTok", "YouTube"} and ("mistakes" in lowered or "compare" in lowered):
            return "high"
        if platform in {"Reddit", "X"} and ("worth" in lowered or "confusing" in lowered or "anxiety" in lowered):
            return "high"
        return "medium"

    @staticmethod
    def _reply_potential(platform: str, text: str) -> str:
        lowered = text.lower()
        if platform == "Reddit" and ("asking" in lowered or "confusing" in lowered):
            return "high"
        if platform == "X" and "debate" in lowered:
            return "medium"
        if platform == "TikTok" and "react" in lowered:
            return "medium"
        return "low"

    @staticmethod
    def _feed(signals: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "time": item["normalized_at"],
                "signal_id": item["signal_id"],
                "platform": item["platform"],
                "source_signal_type": item["source_signal_type"],
                "language": item["language"],
                "market": item["market"],
                "emotion": item["emotion"],
                "trend_strength": item["trend_strength"],
                "engagement_potential": item["engagement_potential"],
                "content_potential": item["content_potential"],
                "reply_potential": item["reply_potential"],
                "topic": item["topic"],
                "why_unified": item["why_unified"],
            }
            for item in signals
        ]


if __name__ == "__main__":
    result = APISignalNormalization().normalize()
    print(json.dumps({"status": result["status"], "signals": result["normalizationSummary"]["signals_normalized"]}, indent=2))
