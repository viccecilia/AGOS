from __future__ import annotations

import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.collection_compliance_guard import CollectionComplianceGuard


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        guard = CollectionComplianceGuard(Path(tmp) / "compliance_guard")
        safe_events = [
            {
                "event_id": "SAFE-001",
                "platform": "Reddit",
                "query": "Tokyo transport anxiety",
                "operation": "trend search",
                "minute_bucket": "2026-05-26T10:00",
                "polling_window": "window-1",
                "write_api_used": False,
                "automated_login_scrape": False,
                "bypass_platform_limits": False,
                "auto_interaction": False,
            },
            {
                "event_id": "SAFE-002",
                "platform": "YouTube",
                "query": "IC card vs rail pass",
                "operation": "public analytics",
                "minute_bucket": "2026-05-26T10:01",
                "polling_window": "window-1",
                "write_api_used": False,
                "automated_login_scrape": False,
                "bypass_platform_limits": False,
                "auto_interaction": False,
            },
        ]
        safe_report = guard.evaluate(safe_events)
        safe_summary = safe_report["complianceGuardSummary"]
        assert safe_report["status"] == "compliance_guard_ready"
        assert safe_summary["guard_ready"] is True
        assert safe_summary["blocking_risk"] is False
        assert safe_summary["read_only_collection_allowed"] is True
        assert safe_summary["write_api_allowed"] is False
        assert safe_summary["automated_login_scrape_allowed"] is False
        assert safe_summary["platform_limit_bypass_allowed"] is False
        assert safe_summary["auto_interaction_allowed"] is False

        risky_events = safe_events + [
            {
                "event_id": "RISK-001",
                "platform": "Reddit",
                "query": "Tokyo transport anxiety",
                "operation": "write_api",
                "minute_bucket": "2026-05-26T10:00",
                "polling_window": "window-1",
                "write_api_used": True,
                "automated_login_scrape": False,
                "bypass_platform_limits": False,
                "auto_interaction": True,
            },
            {
                "event_id": "RISK-002",
                "platform": "TikTok",
                "query": "Tokyo first trip mistakes",
                "operation": "hashtag search",
                "minute_bucket": "2026-05-26T10:00",
                "polling_window": "window-2",
                "write_api_used": False,
                "automated_login_scrape": True,
                "bypass_platform_limits": True,
                "auto_interaction": False,
            },
        ]
        risky_report = guard.evaluate(risky_events)
        risk_types = {item["risk_type"] for item in risky_report["complianceRiskFeed"]}
        risky_summary = risky_report["complianceGuardSummary"]

        assert "write API usage" in risk_types
        assert "automated login scraping" in risk_types
        assert "platform-limit bypass" in risk_types
        assert "automated interaction" in risk_types
        assert risky_summary["blocking_risk"] is True
        assert risky_summary["read_only_collection_allowed"] is False
        assert risky_summary["write_api_allowed"] is False
        assert risky_summary["post_enabled"] is False
        assert risky_summary["reply_enabled"] is False
        assert risky_summary["dm_enabled"] is False
        assert risky_summary["follow_enabled"] is False
        assert risky_summary["like_enabled"] is False
        assert all(item["write_operations_enabled"] is False for item in risky_report["complianceRiskFeed"])

        root = Path(tmp) / "compliance_guard"
        assert (root / "COLLECTION_COMPLIANCE_GUARD_REPORT.json").exists()
        assert (root / "compliance_risk_feed.json").exists()
        assert (root / "compliance_guard_summary.json").exists()
        assert (root / "compliance_events.json").exists()

    print("collection_compliance_guard_smoke_test passed")


if __name__ == "__main__":
    main()
