"""Platform API capability registry for AGOS scout integration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.runtime_persistence import utc_now_iso


PLATFORMS = ["Reddit", "YouTube", "X", "TikTok", "Instagram", "Threads"]
ALLOWED_CAPABILITIES = [
    "trend search",
    "keyword search",
    "public analytics",
    "hashtag search",
    "public comments",
    "account analytics",
]
FORBIDDEN_CAPABILITIES = [
    "auto posting",
    "auto reply",
    "auto follow",
    "auto DM",
    "auto engagement",
]


class APICapabilityRegistry:
    """Describe what platform APIs may and may not be used for."""

    def __init__(self, root: str | Path = "runtime/api_registry") -> None:
        self.root = Path(root)
        self.report_path = self.root / "API_CAPABILITY_REGISTRY.json"
        self.matrix_path = self.root / "platform_api_matrix.json"
        self.feed_path = self.root / "api_capability_feed.json"

    def build(self) -> dict[str, Any]:
        platforms = [self._platform_record(name) for name in PLATFORMS]
        report = {
            "report_id": "API_CAPABILITY_REGISTRY",
            "created_at": utc_now_iso(),
            "status": "registry_ready",
            "scope": "platform_api_capability_boundary_only",
            "platformApiRegistry": platforms,
            "apiCapabilityFeed": self._feed(platforms),
            "apiRegistrySummary": {
                "platforms": len(platforms),
                "allowed_capabilities": len(ALLOWED_CAPABILITIES),
                "forbidden_capabilities": len(FORBIDDEN_CAPABILITIES),
                "all_platforms_block_auto_posting": all("auto posting" in item["forbidden"] for item in platforms),
                "all_platforms_block_auto_reply": all("auto reply" in item["forbidden"] for item in platforms),
                "external_api_calls_enabled": False,
            },
            "safetyBoundary": "This registry only documents API boundaries. It does not call platform APIs, post, reply, follow, DM, or trigger engagement.",
        }
        self.persist(report)
        return report

    def state(self) -> dict[str, Any]:
        if self.report_path.exists():
            return json.loads(self.report_path.read_text(encoding="utf-8"))
        return self.build()

    def persist(self, report: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.matrix_path.write_text(json.dumps(report["platformApiRegistry"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.feed_path.write_text(json.dumps(report["apiCapabilityFeed"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    @staticmethod
    def _platform_record(platform: str) -> dict[str, Any]:
        return {
            "platform": platform,
            "allowed": list(ALLOWED_CAPABILITIES),
            "forbidden": list(FORBIDDEN_CAPABILITIES),
            "allowed_use": "Scout discovery, trend reading, keyword discovery, public signal analysis, and manual review support.",
            "forbidden_use": "No automated posting, replying, following, direct messaging, or engagement manipulation.",
            "requires_human_review": True,
            "credentials_required_for_account_analytics": platform in {"YouTube", "X", "TikTok", "Instagram", "Threads"},
            "api_call_status": "not_connected",
            "execution_boundary": "capability registry only; no external API call",
        }

    @staticmethod
    def _feed(platforms: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "time": utc_now_iso(),
                "platform": item["platform"],
                "allowed": item["allowed"],
                "forbidden": item["forbidden"],
                "status": item["api_call_status"],
                "human_review": item["requires_human_review"],
                "boundary": item["execution_boundary"],
            }
            for item in platforms
        ]


if __name__ == "__main__":
    result = APICapabilityRegistry().build()
    print(json.dumps({"status": result["status"], "platforms": result["apiRegistrySummary"]["platforms"]}, indent=2))
