from __future__ import annotations

import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.api_capability_registry import (
    ALLOWED_CAPABILITIES,
    FORBIDDEN_CAPABILITIES,
    PLATFORMS,
    APICapabilityRegistry,
)


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "api_registry"
        report = APICapabilityRegistry(root).build()

        assert report["report_id"] == "API_CAPABILITY_REGISTRY"
        assert report["status"] == "registry_ready"
        assert report["scope"] == "platform_api_capability_boundary_only"
        assert report["apiRegistrySummary"]["platforms"] == len(PLATFORMS)
        assert report["apiRegistrySummary"]["external_api_calls_enabled"] is False
        assert report["apiRegistrySummary"]["all_platforms_block_auto_posting"] is True
        assert report["apiRegistrySummary"]["all_platforms_block_auto_reply"] is True

        platforms = {item["platform"] for item in report["platformApiRegistry"]}
        assert set(PLATFORMS) == platforms
        for item in report["platformApiRegistry"]:
            assert set(ALLOWED_CAPABILITIES).issubset(set(item["allowed"]))
            assert set(FORBIDDEN_CAPABILITIES).issubset(set(item["forbidden"]))
            assert item["requires_human_review"] is True
            assert item["api_call_status"] == "not_connected"
            assert item["execution_boundary"] == "capability registry only; no external API call"

        assert report["apiCapabilityFeed"], "capability feed is required"
        assert (root / "API_CAPABILITY_REGISTRY.json").exists()
        assert (root / "platform_api_matrix.json").exists()
        assert (root / "api_capability_feed.json").exists()

    print("api capability registry smoke test passed")


if __name__ == "__main__":
    main()
