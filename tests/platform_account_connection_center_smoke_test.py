from __future__ import annotations

import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.api_capability_registry import PLATFORMS
from services.platform_account_connection_center import PlatformAccountConnectionCenter


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        report = PlatformAccountConnectionCenter(Path(tmp) / "platform_connections").build("JAG-LAB")
        connections = report["platformConnections"]
        summary = report["platformConnectionSummary"]
        platforms = {item["platform"] for item in connections}

        assert report["status"] == "connection_center_ready"
        assert platforms == set(PLATFORMS)
        assert summary["platforms"] == 6
        assert summary["connection_center_ready"] is True
        assert summary["all_write_permissions_false"] is True
        assert summary["write_enabled"] == 0
        assert all(item["write_permission"] is False for item in connections)
        assert all("workspace_scope" in item and item["workspace_scope"].startswith("JAG-LAB:") for item in connections)
        assert all("token_expiration" in item for item in connections)
        assert all("read_permission" in item for item in connections)
        assert all(item["connection_status"] in {"read_connected", "not_connected"} for item in connections)
        assert any(item["read_permission"] is True for item in connections)
        assert any(item["read_permission"] is False for item in connections)

        root = Path(tmp) / "platform_connections"
        assert (root / "PLATFORM_ACCOUNT_CONNECTION_CENTER.json").exists()
        assert (root / "platform_connections.json").exists()
        assert (root / "platform_connection_feed.json").exists()
        assert (root / "platform_connection_summary.json").exists()

    print("platform_account_connection_center_smoke_test passed")


if __name__ == "__main__":
    main()
