"""Daily operations report for AGOS Real Operations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.best_answer_learning_engine import BestAnswerLearningEngine
from services.daily_question_import_engine import DailyQuestionImportEngine
from services.real_feedback_capture_engine import RealFeedbackCaptureEngine
from services.real_reply_attempt_engine import RealReplyAttemptEngine
from services.runtime_persistence import utc_now_iso


class DailyOperationsReportEngine:
    """Generate a daily report from real operations runtime artifacts."""

    def __init__(self, root: str | Path = "runtime/daily_reports") -> None:
        self.root = Path(root)
        self.report_path = self.root / "DAILY_OPERATIONS_REPORT.json"
        self.feed_path = self.root / "runtime_daily_report_feed.json"

    def generate(self) -> dict[str, Any]:
        daily_import = DailyQuestionImportEngine().state()
        reply_attempts = RealReplyAttemptEngine().state()
        feedback = RealFeedbackCaptureEngine().state()
        learning = BestAnswerLearningEngine().state()
        feed = self._feed(daily_import, reply_attempts, feedback, learning)
        report = {
            "report_id": "DAILY_OPERATIONS_REPORT",
            "created_at": utc_now_iso(),
            "status": "active",
            "scope": "local_daily_report_only",
            "todayImportedQuestions": daily_import.get("dailyQuestions", []),
            "todayReplies": reply_attempts.get("replyAttempts", []),
            "todayHighEngagement": [event for event in feedback.get("feedbackEvents", []) if event.get("has_positive_feedback")],
            "todayIgnored": [event for event in feedback.get("feedbackEvents", []) if event.get("has_negative_feedback")],
            "todayBestContent": learning.get("bestAnswerLearning", {}).get("bestHook", "none"),
            "todayBestReply": learning.get("bestAnswerLearning", {}).get("bestAnswer"),
            "runtimeDailyReportFeed": feed,
            "dailyOperationsSummary": {
                "imported_questions": len(daily_import.get("dailyQuestions", [])),
                "reply_drafts": len(reply_attempts.get("replyAttempts", [])),
                "high_engagement": len([event for event in feedback.get("feedbackEvents", []) if event.get("has_positive_feedback")]),
                "ignored": len([event for event in feedback.get("feedbackEvents", []) if event.get("has_negative_feedback")]),
                "best_reply_id": (learning.get("bestAnswerLearning", {}).get("bestAnswer") or {}).get("reply_attempt_id", "none"),
                "best_hook": learning.get("bestAnswerLearning", {}).get("bestHook", "none"),
            },
        }
        self.persist(report)
        return report

    def state(self) -> dict[str, Any]:
        if self.report_path.exists():
            return json.loads(self.report_path.read_text(encoding="utf-8"))
        return self.generate()

    def persist(self, report: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.feed_path.write_text(json.dumps(report["runtimeDailyReportFeed"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    @staticmethod
    def _feed(
        daily_import: dict[str, Any],
        reply_attempts: dict[str, Any],
        feedback: dict[str, Any],
        learning: dict[str, Any],
    ) -> list[dict[str, Any]]:
        summary = []
        summary.append(
            {
                "type": "imported_questions",
                "title": "今天导入问题",
                "value": len(daily_import.get("dailyQuestions", [])),
                "detail": "Daily Question Import completed.",
            }
        )
        summary.append(
            {
                "type": "reply_drafts",
                "title": "今天回复",
                "value": len(reply_attempts.get("replyAttempts", [])),
                "detail": "Reply drafts generated and waiting for human review.",
            }
        )
        summary.append(
            {
                "type": "high_engagement",
                "title": "今天高互动",
                "value": len([event for event in feedback.get("feedbackEvents", []) if event.get("has_positive_feedback")]),
                "detail": "Feedback events with liked/replied/saved/shared.",
            }
        )
        summary.append(
            {
                "type": "ignored",
                "title": "今天被忽视",
                "value": len([event for event in feedback.get("feedbackEvents", []) if event.get("has_negative_feedback")]),
                "detail": "Feedback events marked ignored without positive signal.",
            }
        )
        best = learning.get("bestAnswerLearning", {})
        summary.append(
            {
                "type": "best_content",
                "title": "今天最佳内容",
                "value": best.get("bestHook", "none"),
                "detail": best.get("bestTone", "none"),
            }
        )
        summary.append(
            {
                "type": "best_reply",
                "title": "今天最佳回复",
                "value": (best.get("bestAnswer") or {}).get("reply_attempt_id", "none"),
                "detail": (best.get("bestAnswer") or {}).get("answer_pattern", "none"),
            }
        )
        return summary


if __name__ == "__main__":
    result = DailyOperationsReportEngine().generate()
    print(json.dumps({"status": result["status"], "items": len(result["runtimeDailyReportFeed"])}, indent=2))
