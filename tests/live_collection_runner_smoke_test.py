from __future__ import annotations

import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.live_collection_runner import LiveCollectionRunner


def main() -> None:
    sources = [
        {
            "platform": "Reddit",
            "source_type": "public_trend_import",
            "query": "Tokyo transport anxiety",
            "keyword": "Tokyo subway confusing",
            "hashtag": "japantravel",
            "public_metric": {"mentions": 12, "comments": 8, "score": 60},
            "trend_text": "Visitors ask how to choose the right transport pass.",
        },
        {
            "platform": "TikTok",
            "source_type": "public_hashtag_import",
            "query": "Tokyo first trip mistakes",
            "keyword": "airport transfer confusion",
            "hashtag": "tokyotravel",
            "public_metric": {"mentions": 20, "comments": 11, "score": 72},
            "trend_text": "Short videos discuss airport transfer confusion.",
        },
    ]
    with tempfile.TemporaryDirectory() as tmp:
        runner = LiveCollectionRunner(Path(tmp) / "live_collection")
        report = runner.run("JAG-LAB", sources)
        summary = report["liveCollectionSummary"]
        items = report["liveCollectionItems"]

        assert report["report_id"] == "LIVE_COLLECTION_RUNNER_REPORT"
        assert report["status"] == "live_collection_completed"
        assert set(report["supportedCollectionModes"]) == {
            "trend search",
            "keyword search",
            "hashtag search",
            "public analytics",
        }
        assert set(report["forbiddenLiveActions"]) == {"post", "reply", "DM", "follow", "like"}
        assert summary["runner_ready"] is True
        assert summary["items_collected"] == 2
        assert summary["read_only"] is True
        assert summary["public_intelligence_only"] is True
        assert summary["write_operations_enabled"] is False
        assert summary["post_enabled"] is False
        assert summary["reply_enabled"] is False
        assert summary["dm_enabled"] is False
        assert summary["follow_enabled"] is False
        assert summary["like_enabled"] is False
        assert summary["all_write_actions_blocked"] is True
        assert all(item["read_status"] == "collected" for item in items)
        assert all(item["write_status"] == "blocked" for item in items)
        assert all(item["post_enabled"] is False for item in items)
        assert all(item["reply_enabled"] is False for item in items)
        assert all(item["dm_enabled"] is False for item in items)
        assert all(item["follow_enabled"] is False for item in items)
        assert all(item["like_enabled"] is False for item in items)

        root = Path(tmp) / "live_collection"
        assert (root / "LIVE_COLLECTION_RUNNER_REPORT.json").exists()
        assert (root / "live_collection_items.json").exists()
        assert (root / "live_collection_feed.json").exists()
        assert (root / "live_collection_summary.json").exists()

    print("live_collection_runner_smoke_test passed")


if __name__ == "__main__":
    main()
