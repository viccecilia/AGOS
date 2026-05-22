from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.daily_question_import_engine import DailyQuestionImportEngine
from services.real_reply_attempt_engine import RealReplyAttemptEngine


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        daily = DailyQuestionImportEngine(Path(tmp) / "daily_question_import").import_today(import_date="2026-05-22")
        engine = RealReplyAttemptEngine(Path(tmp) / "real_reply_attempts")
        report = engine.generate_attempts(daily["dailyQuestions"])

        assert report["report_id"] == "REAL_REPLY_ATTEMPTS_REPORT"
        assert report["status"] == "active"
        assert report["scope"] == "local_draft_only_no_auto_reply"
        assert set(report["supportedPlatforms"]) == {"Reddit", "TikTok", "X"}
        assert report["replyAttemptSummary"]["source_questions"] == 6
        assert report["replyAttemptSummary"]["total_attempts"] == 18
        assert report["replyAttemptSummary"]["needs_human_review"] == 18
        assert len(report["replyReviewQueue"]) == 18

        attempts = report["replyAttempts"]
        assert any(attempt["platform"] == "Reddit" for attempt in attempts)
        assert any(attempt["platform"] == "TikTok" for attempt in attempts)
        assert any(attempt["platform"] == "X" for attempt in attempts)
        assert all(attempt["review_status"] == "needs_human_review" for attempt in attempts)
        assert all("no_auto_reply" in attempt["prohibited_actions"] for attempt in attempts)
        assert all("human review" in attempt["reply_text"].lower() for attempt in attempts)

        first = attempts[0]["reply_attempt_id"]
        approved = engine.approve(first)
        assert approved["decision"] == "approved"

        second = attempts[1]["reply_attempt_id"]
        rejected = engine.reject(second, "Too generic for TikTok.")
        assert rejected["decision"] == "rejected"
        assert rejected["details"]["reject_reason"] == "Too generic for TikTok."

        third = attempts[2]["reply_attempt_id"]
        modified = engine.modify(third, "Use one simple station route and one backup. Human approved wording.")
        assert modified["decision"] == "modified"
        assert "Human approved" in modified["details"]["human_modified_version"]

        saved = json.loads((Path(tmp) / "real_reply_attempts" / "REAL_REPLY_ATTEMPTS_REPORT.json").read_text(encoding="utf-8"))
        assert saved["replyAttemptSummary"]["needs_human_review"] == 15
        decisions = json.loads((Path(tmp) / "real_reply_attempts" / "reply_review_decisions.json").read_text(encoding="utf-8"))
        assert [item["decision"] for item in decisions] == ["approved", "rejected", "modified"]

    print("real reply attempts smoke test passed")


if __name__ == "__main__":
    main()
