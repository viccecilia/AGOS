"""Read-only platform trend connector for AGOS scout integration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.api_capability_registry import APICapabilityRegistry
from services.runtime_persistence import utc_now_iso


READ_ONLY_CAPABILITIES = {"trend search", "keyword search", "hashtag search", "public analytics"}
FORBIDDEN_OPERATIONS = {"post", "reply", "follow", "DM"}

DEFAULT_TREND_INPUTS = [
    {
        "platform": "Reddit",
        "source_type": "public_trend_import",
        "query": "Tokyo transport anxiety",
        "keyword": "Tokyo subway confusing",
        "hashtag": "japantravel",
        "public_metric": {"mentions": 42, "comments": 18, "score": 78},
        "trend_text": "Travelers are asking how to choose the right Tokyo transport pass.",
    },
    {
        "platform": "YouTube",
        "source_type": "public_trend_import",
        "query": "Japan travel planning",
        "keyword": "IC card vs rail pass",
        "hashtag": "japantrip",
        "public_metric": {"mentions": 31, "comments": 9, "score": 61},
        "trend_text": "Short videos compare Suica, Pasmo, and JR Pass choices.",
    },
    {
        "platform": "TikTok",
        "source_type": "public_trend_import",
        "query": "Tokyo first trip mistakes",
        "keyword": "airport transfer confusion",
        "hashtag": "tokyotravel",
        "public_metric": {"mentions": 54, "comments": 21, "score": 84},
        "trend_text": "First-time travelers react strongly to airport transfer complexity.",
    },
    {
        "platform": "X",
        "source_type": "public_trend_import",
        "query": "Japan train pass",
        "keyword": "JR Pass worth it",
        "hashtag": "JapanTravel",
        "public_metric": {"mentions": 27, "comments": 7, "score": 55},
        "trend_text": "Users debate whether JR Pass still saves money after price changes.",
    },
]


class ReadOnlyTrendConnector:
    """Read and normalize trend signals without any write-side platform action."""

    def __init__(self, root: str | Path = "runtime/platform_trends") -> None:
        self.root = Path(root)
        self.report_path = self.root / "READ_ONLY_TREND_REPORT.json"
        self.trends_path = self.root / "platform_trends.json"
        self.feed_path = self.root / "platform_trend_feed.json"

    def read_trends(self, inputs: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        registry = APICapabilityRegistry().state()
        platform_capabilities = {
            item["platform"]: set(item.get("allowed", []))
            for item in registry.get("platformApiRegistry", [])
        }
        source_items = inputs if inputs is not None else DEFAULT_TREND_INPUTS
        trends = [
            self._normalize(index, item, platform_capabilities.get(item.get("platform", ""), set()))
            for index, item in enumerate(source_items, start=1)
        ]
        report = {
            "report_id": "READ_ONLY_TREND_REPORT",
            "created_at": utc_now_iso(),
            "status": "trends_read",
            "scope": "read_only_platform_trend_connector",
            "supportedReadCapabilities": sorted(READ_ONLY_CAPABILITIES),
            "forbiddenOperations": sorted(FORBIDDEN_OPERATIONS),
            "platformTrends": trends,
            "platformTrendFeed": self._feed(trends),
            "trendConnectorSummary": {
                "trends_read": len(trends),
                "platforms": len({item["platform"] for item in trends}),
                "read_only": True,
                "write_operations_enabled": False,
                "post_enabled": False,
                "reply_enabled": False,
                "follow_enabled": False,
                "dm_enabled": False,
                "source_mode": "read_only_public_trend_import",
            },
            "safetyBoundary": "Connector reads and normalizes trend inputs only. It cannot post, reply, follow, DM, or trigger engagement.",
        }
        self.persist(report)
        return report

    def state(self) -> dict[str, Any]:
        if self.report_path.exists():
            return json.loads(self.report_path.read_text(encoding="utf-8"))
        return self.read_trends()

    def persist(self, report: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.trends_path.write_text(json.dumps(report["platformTrends"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.feed_path.write_text(json.dumps(report["platformTrendFeed"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    @staticmethod
    def _normalize(index: int, item: dict[str, Any], allowed: set[str]) -> dict[str, Any]:
        missing = sorted(READ_ONLY_CAPABILITIES - allowed)
        metric = item.get("public_metric", {})
        heat_score = min(int(metric.get("score", 0)) + int(metric.get("comments", 0)), 100)
        return {
            "trend_id": f"TREND-{index:04d}",
            "platform": item.get("platform", "unknown"),
            "source_type": item.get("source_type", "public_trend_import"),
            "query": item.get("query", ""),
            "keyword": item.get("keyword", ""),
            "hashtag": item.get("hashtag", ""),
            "trend_text": item.get("trend_text", ""),
            "public_metric": metric,
            "heat_score": heat_score,
            "read_capabilities_used": sorted(READ_ONLY_CAPABILITIES & allowed) or sorted(READ_ONLY_CAPABILITIES),
            "missing_registry_capabilities": missing,
            "read_status": "read",
            "write_status": "blocked",
            "human_review_required": True,
            "ingested_at": utc_now_iso(),
            "execution_boundary": "read-only trend connector; no platform write action",
        }

    @staticmethod
    def _feed(trends: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "time": item["ingested_at"],
                "trend_id": item["trend_id"],
                "platform": item["platform"],
                "query": item["query"],
                "keyword": item["keyword"],
                "hashtag": item["hashtag"],
                "heat_score": item["heat_score"],
                "read_status": item["read_status"],
                "write_status": item["write_status"],
                "trend_text": item["trend_text"],
            }
            for item in trends
        ]


if __name__ == "__main__":
    result = ReadOnlyTrendConnector().read_trends()
    print(json.dumps({"status": result["status"], "trends": result["trendConnectorSummary"]["trends_read"]}, indent=2))
