from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.daily_operations_report_engine import DailyOperationsReportEngine


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        engine = DailyOperationsReportEngine(Path(tmp) / "daily_reports")
        report = engine.generate()

        assert report["report_id"] == "DAILY_OPERATIONS_REPORT"
        assert report["status"] == "active"
        assert report["scope"] == "local_daily_report_only"
        assert len(report["todayImportedQuestions"]) >= 10
        assert report["todayReplies"]
        assert report["todayHighEngagement"]
        assert report["todayIgnored"]
        assert report["todayBestContent"] != "none"
        assert report["todayBestReply"]

        feed = report["runtimeDailyReportFeed"]
        feed_types = {item["type"] for item in feed}
        assert {
            "imported_questions",
            "reply_drafts",
            "high_engagement",
            "ignored",
            "best_content",
            "best_reply",
        }.issubset(feed_types)
        assert report["dailyOperationsSummary"]["imported_questions"] >= 10
        assert report["dailyOperationsSummary"]["reply_drafts"] >= 1
        assert report["dailyOperationsSummary"]["high_engagement"] >= 1
        assert report["dailyOperationsSummary"]["ignored"] >= 1

        assert (Path(tmp) / "daily_reports" / "DAILY_OPERATIONS_REPORT.json").exists()
        assert (Path(tmp) / "daily_reports" / "runtime_daily_report_feed.json").exists()
        saved = json.loads((Path(tmp) / "daily_reports" / "DAILY_OPERATIONS_REPORT.json").read_text(encoding="utf-8"))
        assert saved["dailyOperationsSummary"]["best_reply_id"] != "none"

    print("daily operations report smoke test passed")


if __name__ == "__main__":
    main()
