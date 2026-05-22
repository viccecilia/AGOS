from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.daily_question_import_engine import DailyQuestionImportEngine
from services.real_feedback_capture_engine import RealFeedbackCaptureEngine
from services.real_reply_attempt_engine import RealReplyAttemptEngine


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        daily = DailyQuestionImportEngine(Path(tmp) / "daily_question_import").import_today(import_date="2026-05-22")
        replies = RealReplyAttemptEngine(Path(tmp) / "real_reply_attempts").generate_attempts(daily["dailyQuestions"])
        attempts = replies["replyAttempts"]
        feedback_events = [
            {
                "reply_attempt_id": attempts[0]["reply_attempt_id"],
                "liked": True,
                "replied": True,
                "feedback_note": "Follow-up question received.",
            },
            {
                "reply_attempt_id": attempts[1]["reply_attempt_id"],
                "ignored": True,
                "feedback_note": "No response after review window.",
            },
            {
                "reply_attempt_id": attempts[2]["reply_attempt_id"],
                "saved": True,
                "shared": True,
                "feedback_note": "Saved as useful route tip.",
            },
        ]
        engine = RealFeedbackCaptureEngine(Path(tmp) / "feedback_capture")
        report = engine.capture(feedback_events)

        assert report["report_id"] == "REAL_FEEDBACK_CAPTURE_REPORT"
        assert report["status"] == "active"
        assert report["scope"] == "local_feedback_record_only_no_platform_api"
        assert set(report["feedbackSignals"]) == {"liked", "replied", "ignored", "saved", "shared"}
        assert len(report["feedbackEvents"]) == 3
        assert len(report["feedbackTimeline"]) == 3
        assert report["feedbackSummary"]["liked"] == 1
        assert report["feedbackSummary"]["replied"] == 1
        assert report["feedbackSummary"]["ignored"] == 1
        assert report["feedbackSummary"]["saved"] == 1
        assert report["feedbackSummary"]["shared"] == 1
        assert report["feedbackSummary"]["positive_feedback"] == 2
        assert report["feedbackSummary"]["ignored_feedback"] == 1
        assert any(event["has_positive_feedback"] for event in report["feedbackEvents"])
        assert any(event["has_negative_feedback"] for event in report["feedbackEvents"])

        recorded = engine.record_feedback(
            attempts[3]["reply_attempt_id"],
            {"liked": True, "saved": True},
            "Manually recorded useful reply.",
        )
        assert recorded["liked"] is True
        assert recorded["saved"] is True

        saved = json.loads((Path(tmp) / "feedback_capture" / "REAL_FEEDBACK_CAPTURE_REPORT.json").read_text(encoding="utf-8"))
        assert saved["feedbackSummary"]["total_feedback_events"] == 4
        assert (Path(tmp) / "feedback_capture" / "feedback_events.json").exists()
        assert (Path(tmp) / "feedback_capture" / "feedback_timeline.json").exists()

    print("real feedback capture smoke test passed")


if __name__ == "__main__":
    main()
