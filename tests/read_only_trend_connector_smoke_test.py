from __future__ import annotations

import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.read_only_trend_connector import ReadOnlyTrendConnector


def main() -> None:
    inputs = [
        {
            "platform": "Reddit",
            "source_type": "public_trend_import",
            "query": "Tokyo subway confusing",
            "keyword": "Tokyo transport",
            "hashtag": "japantravel",
            "public_metric": {"mentions": 10, "comments": 5, "score": 50},
            "trend_text": "Travelers ask how to avoid Tokyo station mistakes.",
        },
        {
            "platform": "TikTok",
            "source_type": "public_trend_import",
            "query": "Japan airport transfer",
            "keyword": "Narita to Tokyo",
            "hashtag": "tokyotravel",
            "public_metric": {"mentions": 20, "comments": 11, "score": 70},
            "trend_text": "Airport transfer videos are getting high comments.",
        },
    ]
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "platform_trends"
        connector = ReadOnlyTrendConnector(root)
        report = connector.read_trends(inputs)

        assert report["report_id"] == "READ_ONLY_TREND_REPORT"
        assert report["status"] == "trends_read"
        assert report["scope"] == "read_only_platform_trend_connector"
        assert report["trendConnectorSummary"]["trends_read"] == 2
        assert report["trendConnectorSummary"]["read_only"] is True
        assert report["trendConnectorSummary"]["write_operations_enabled"] is False
        assert report["trendConnectorSummary"]["post_enabled"] is False
        assert report["trendConnectorSummary"]["reply_enabled"] is False
        assert report["trendConnectorSummary"]["follow_enabled"] is False
        assert report["trendConnectorSummary"]["dm_enabled"] is False
        assert {"trend search", "keyword search", "hashtag search", "public analytics"}.issubset(
            set(report["supportedReadCapabilities"])
        )
        assert {"post", "reply", "follow", "DM"}.issubset(set(report["forbiddenOperations"]))

        for item in report["platformTrends"]:
            assert item["read_status"] == "read"
            assert item["write_status"] == "blocked"
            assert item["heat_score"] > 0
            assert item["execution_boundary"] == "read-only trend connector; no platform write action"

        assert not hasattr(connector, "post")
        assert not hasattr(connector, "reply")
        assert not hasattr(connector, "follow")
        assert not hasattr(connector, "dm")
        assert (root / "READ_ONLY_TREND_REPORT.json").exists()
        assert (root / "platform_trends.json").exists()
        assert (root / "platform_trend_feed.json").exists()

    print("read only trend connector smoke test passed")


if __name__ == "__main__":
    main()
