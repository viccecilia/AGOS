"""Read-only live collection runner for controlled public intelligence intake."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.api_capability_registry import APICapabilityRegistry, PLATFORMS
from services.read_only_trend_connector import DEFAULT_TREND_INPUTS, READ_ONLY_CAPABILITIES
from services.runtime_persistence import utc_now_iso


FORBIDDEN_LIVE_ACTIONS = ("post", "reply", "DM", "follow", "like")
SUPPORTED_COLLECTION_MODES = ("trend search", "keyword search", "hashtag search", "public analytics")


class LiveCollectionRunner:
    """Run read-only public intelligence collection without platform write actions."""

    def __init__(self, root: str | Path = "runtime/live_collection") -> None:
        self.root = Path(root)
        self.report_path = self.root / "LIVE_COLLECTION_RUNNER_REPORT.json"
        self.items_path = self.root / "live_collection_items.json"
        self.feed_path = self.root / "live_collection_feed.json"
        self.summary_path = self.root / "live_collection_summary.json"

    def run(
        self,
        workspace_id: str = "JAG-LAB",
        sources: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        registry = APICapabilityRegistry().state()
        capabilities_by_platform = {
            item["platform"]: set(item.get("allowed", []))
            for item in registry.get("platformApiRegistry", [])
        }
        source_items = sources if sources is not None else DEFAULT_TREND_INPUTS
        collection_items = [
            self._collect_item(index, workspace_id, item, capabilities_by_platform.get(item.get("platform", ""), set()))
            for index, item in enumerate(source_items, start=1)
        ]
        report = {
            "report_id": "LIVE_COLLECTION_RUNNER_REPORT",
            "created_at": utc_now_iso(),
            "status": "live_collection_completed",
            "scope": "controlled_read_only_public_intelligence_collection",
            "workspace_id": workspace_id,
            "supportedCollectionModes": list(SUPPORTED_COLLECTION_MODES),
            "forbiddenLiveActions": list(FORBIDDEN_LIVE_ACTIONS),
            "platformCoverage": self._platform_coverage(collection_items),
            "liveCollectionItems": collection_items,
            "liveCollectionFeed": self._feed(collection_items),
            "liveCollectionSummary": self._summary(collection_items),
            "safetyBoundary": "Live Collection Runner reads public intelligence signals only. It does not post, reply, DM, follow, like, log in, register accounts, bypass platform limits, or call write-side APIs.",
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
        self.items_path.write_text(json.dumps(report["liveCollectionItems"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.feed_path.write_text(json.dumps(report["liveCollectionFeed"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.summary_path.write_text(json.dumps(report["liveCollectionSummary"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    @staticmethod
    def _collect_item(index: int, workspace_id: str, item: dict[str, Any], allowed: set[str]) -> dict[str, Any]:
        metric = item.get("public_metric", {})
        read_capabilities = sorted(set(SUPPORTED_COLLECTION_MODES) & allowed) or sorted(READ_ONLY_CAPABILITIES)
        collection_score = min(
            int(metric.get("score", 0))
            + int(metric.get("comments", 0))
            + int(metric.get("mentions", 0)) // 3,
            100,
        )
        return {
            "collection_id": f"LIVE-COLLECT-{index:04d}",
            "workspace_id": workspace_id,
            "platform": item.get("platform", "unknown"),
            "source_type": item.get("source_type", "public_trend_import"),
            "collection_modes_used": read_capabilities,
            "query": item.get("query", ""),
            "keyword": item.get("keyword", ""),
            "hashtag": item.get("hashtag", ""),
            "public_metric": metric,
            "public_signal_text": item.get("trend_text", ""),
            "collection_score": collection_score,
            "read_status": "collected",
            "write_status": "blocked",
            "post_enabled": False,
            "reply_enabled": False,
            "dm_enabled": False,
            "follow_enabled": False,
            "like_enabled": False,
            "requires_human_review": True,
            "collected_at": utc_now_iso(),
            "execution_boundary": "read-only live collection; public intelligence only",
        }

    @staticmethod
    def _feed(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "time": item["collected_at"],
                "collection_id": item["collection_id"],
                "platform": item["platform"],
                "query": item["query"],
                "keyword": item["keyword"],
                "hashtag": item["hashtag"],
                "collection_score": item["collection_score"],
                "read_status": item["read_status"],
                "write_status": item["write_status"],
                "public_signal_text": item["public_signal_text"],
                "execution_boundary": item["execution_boundary"],
            }
            for item in items
        ]

    @staticmethod
    def _platform_coverage(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen = {item["platform"] for item in items}
        return [
            {
                "platform": platform,
                "covered": platform in seen,
                "collection_status": "collected" if platform in seen else "pending_source",
                "write_actions_blocked": True,
            }
            for platform in PLATFORMS
        ]

    @staticmethod
    def _summary(items: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "runner_ready": True,
            "items_collected": len(items),
            "platforms_collected": len({item["platform"] for item in items}),
            "supported_collection_modes": list(SUPPORTED_COLLECTION_MODES),
            "read_only": True,
            "public_intelligence_only": True,
            "write_operations_enabled": False,
            "post_enabled": False,
            "reply_enabled": False,
            "dm_enabled": False,
            "follow_enabled": False,
            "like_enabled": False,
            "all_write_actions_blocked": all(item["write_status"] == "blocked" for item in items),
        }


if __name__ == "__main__":
    result = LiveCollectionRunner().run()
    print(json.dumps({"status": result["status"], "items": result["liveCollectionSummary"]["items_collected"]}, indent=2))
