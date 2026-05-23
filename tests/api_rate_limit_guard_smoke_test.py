from __future__ import annotations

import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.api_rate_limit_guard import APIRateLimitGuard


def main() -> None:
    events = [
        {
            "event_id": f"EVT-{index:04d}",
            "platform": "Reddit",
            "query": "Tokyo subway confusing",
            "minute_bucket": "2026-05-23T10:00",
            "hour_bucket": "2026-05-23T10",
            "day_bucket": "2026-05-23",
            "operation": "trend search" if index % 2 else "keyword search",
        }
        for index in range(1, 6)
    ]
    events.append(
        {
            "event_id": "EVT-0006",
            "platform": "TikTok",
            "query": "Japan travel mistakes",
            "minute_bucket": "2026-05-23T10:01",
            "hour_bucket": "2026-05-23T10",
            "day_bucket": "2026-05-23",
            "operation": "hashtag search",
        }
    )

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "api_risk"
        guard = APIRateLimitGuard(root=root, limits={"requests_per_minute": 5, "requests_per_hour": 20, "requests_per_day": 100})
        report = guard.evaluate(events)

        assert report["report_id"] == "API_RATE_LIMIT_GUARD_REPORT"
        assert report["status"] == "safety_guard_ready"
        assert report["scope"] == "read_only_api_rate_limit_and_safety_guard"
        assert report["limits"]["requests_per_minute"] == 5
        assert report["apiRiskSummary"]["risk_items"] >= 4
        assert report["apiRiskSummary"]["approaching_platform_risk"] is True
        assert report["apiRiskSummary"]["write_operations_enabled"] is False

        statuses = {item["status"] for item in report["apiRiskFeed"]}
        risk_types = {item["risk_type"] for item in report["apiRiskFeed"]}
        assert "blocked" in statuses
        assert "repeated queries" in risk_types
        assert "requests/minute" in risk_types

        for item in report["apiRiskFeed"]:
            assert item["platform"]
            assert item["why"]
            assert item["recommended_action"]

        assert (root / "API_RATE_LIMIT_GUARD_REPORT.json").exists()
        assert (root / "api_risk_feed.json").exists()
        assert (root / "api_usage_summary.json").exists()

    print("api rate limit guard smoke test passed")


if __name__ == "__main__":
    main()
