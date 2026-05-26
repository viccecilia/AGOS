"""Platform account connection center for controlled API intelligence collection."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.api_capability_registry import PLATFORMS
from services.runtime_persistence import utc_now_iso


READ_CONNECTED = {"Reddit", "YouTube"}


class PlatformAccountConnectionCenter:
    """Track platform API account connection status without enabling write permissions."""

    def __init__(self, root: str | Path = "runtime/platform_connections") -> None:
        self.root = Path(root)
        self.report_path = self.root / "PLATFORM_ACCOUNT_CONNECTION_CENTER.json"
        self.connections_path = self.root / "platform_connections.json"
        self.feed_path = self.root / "platform_connection_feed.json"
        self.summary_path = self.root / "platform_connection_summary.json"

    def build(self, workspace_id: str = "JAG-LAB") -> dict[str, Any]:
        connections = [self._connection_record(platform, workspace_id) for platform in PLATFORMS]
        report = {
            "report_id": "PLATFORM_ACCOUNT_CONNECTION_CENTER",
            "created_at": utc_now_iso(),
            "status": "connection_center_ready",
            "scope": "controlled_api_intelligence_collection",
            "platformConnections": connections,
            "platformConnectionFeed": self._feed(connections),
            "platformConnectionSummary": self._summary(connections),
            "safetyBoundary": "Platform Account Connection Center tracks local connection state only. Write permissions are false by default and no platform API call, post, reply, follow, DM, login, or account registration is performed.",
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
        self.connections_path.write_text(json.dumps(report["platformConnections"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.feed_path.write_text(json.dumps(report["platformConnectionFeed"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.summary_path.write_text(json.dumps(report["platformConnectionSummary"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    @staticmethod
    def _connection_record(platform: str, workspace_id: str) -> dict[str, Any]:
        read_permission = platform in READ_CONNECTED
        return {
            "platform": platform,
            "workspace_id": workspace_id,
            "connection_status": "read_connected" if read_permission else "not_connected",
            "read_permission": read_permission,
            "write_permission": False,
            "token_expiration": "not_configured" if not read_permission else "sample_status_only_no_secret",
            "workspace_scope": f"{workspace_id}:{platform.lower()}:read_only",
            "credential_status": "redacted_status_only" if read_permission else "missing_or_pending_setup",
            "allowed_collection_mode": "read_only_public_intelligence" if read_permission else "manual_import_or_pending_api_setup",
            "blocked_actions": ["post", "reply", "follow", "dm", "auto_engagement", "account_registration"],
            "requires_human_review": True,
            "last_checked_at": utc_now_iso(),
        }

    @staticmethod
    def _summary(connections: list[dict[str, Any]]) -> dict[str, Any]:
        read_connected = [item for item in connections if item["read_permission"]]
        write_enabled = [item for item in connections if item["write_permission"]]
        return {
            "platforms": len(connections),
            "read_connected": len(read_connected),
            "not_connected": len(connections) - len(read_connected),
            "write_enabled": len(write_enabled),
            "all_write_permissions_false": all(item["write_permission"] is False for item in connections),
            "workspace_scopes": [item["workspace_scope"] for item in connections],
            "connection_center_ready": True,
        }

    @staticmethod
    def _feed(connections: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "time": item["last_checked_at"],
                "platform": item["platform"],
                "connection_status": item["connection_status"],
                "read_permission": item["read_permission"],
                "write_permission": item["write_permission"],
                "token_expiration": item["token_expiration"],
                "workspace_scope": item["workspace_scope"],
                "credential_status": item["credential_status"],
                "allowed_collection_mode": item["allowed_collection_mode"],
            }
            for item in connections
        ]


if __name__ == "__main__":
    result = PlatformAccountConnectionCenter().build()
    print(json.dumps({"status": result["status"], "platforms": result["platformConnectionSummary"]["platforms"]}, indent=2))
