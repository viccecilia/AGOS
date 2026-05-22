"""Real growth validation for AGOS Real Operations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.best_answer_learning_engine import BestAnswerLearningEngine
from services.daily_operations_report_engine import DailyOperationsReportEngine
from services.failure_analysis_engine import FailureAnalysisEngine
from services.heat_detection_engine import HeatDetectionEngine
from services.real_feedback_capture_engine import RealFeedbackCaptureEngine
from services.real_reply_attempt_engine import RealReplyAttemptEngine
from services.runtime_engine import RuntimeEngine
from services.runtime_persistence import utc_now_iso
from services.trend_clustering_engine import TrendClusteringEngine


class RealGrowthValidationEngine:
    """Validate whether AGOS has formed real growth intelligence."""

    def __init__(self, root: str | Path = "runtime/real_growth_validation") -> None:
        self.root = Path(root)
        self.report_path = self.root / "REAL_GROWTH_VALIDATION_REPORT.json"
        self.review_path = self.root / "RUNTIME_INTELLIGENCE_REVIEW.json"

    def validate(self) -> dict[str, Any]:
        runtime_state = RuntimeEngine().current_state()
        trend = TrendClusteringEngine().state()
        heat = HeatDetectionEngine().state()
        replies = RealReplyAttemptEngine().state()
        feedback = RealFeedbackCaptureEngine().state()
        learning = BestAnswerLearningEngine().state()
        failures = FailureAnalysisEngine().state()
        daily = DailyOperationsReportEngine().state()
        checks = [
            self._check("runtime_stable", bool(runtime_state.get("pipeline")), "Runtime pipeline exists and can expose state."),
            self._check("scout_effective", bool(trend.get("trendClusters")) and bool(heat.get("opportunityRanking")), "Scout produced trend clusters and heat ranking."),
            self._check("reply_effective", bool(replies.get("replyAttempts")), "Reply drafts exist and are review-gated."),
            self._check("feedback_effective", bool(feedback.get("feedbackEvents")), "Feedback events are captured."),
            self._check("learning_effective", learning.get("learningSummary", {}).get("best_answer_id") != "none", "Best answer learning produced a best answer."),
            self._check("workspace_growth_supported", bool(failures.get("failureItems")), "Failure analysis explains ignored replies and failed patterns."),
        ]
        passed = all(item["status"] == "passed" for item in checks)
        review = {
            "review_id": "RUNTIME_INTELLIGENCE_REVIEW",
            "created_at": utc_now_iso(),
            "growth_intelligence_status": "formed" if passed else "needs_more_real_ops",
            "workspace_growth_signal": self._workspace_growth_signal(daily, feedback, learning, failures),
            "next_stage": "Autonomous Growth Preparation Stage" if passed else "Continue Real Operations",
            "evidence": {
                "daily_report": "runtime/daily_reports/DAILY_OPERATIONS_REPORT.json",
                "feedback_capture": "runtime/feedback_capture/REAL_FEEDBACK_CAPTURE_REPORT.json",
                "best_answer_learning": "runtime/best_answer_learning/BEST_ANSWER_LEARNING_REPORT.json",
                "failure_analysis": "runtime/failure_analysis/FAILURE_ANALYSIS_REPORT.json",
            },
        }
        report = {
            "report_id": "REAL_GROWTH_VALIDATION_REPORT",
            "created_at": utc_now_iso(),
            "status": "passed" if passed else "needs_review",
            "scope": "local_real_operations_validation",
            "validationChecks": checks,
            "workspaceGrowthValidation": {
                "workspace_id": "JAG-LAB",
                "helped_workspace_grow": passed,
                "reason": review["workspace_growth_signal"],
            },
            "realGrowthValidationSummary": {
                "runtime_stable": checks[0]["status"] == "passed",
                "scout_effective": checks[1]["status"] == "passed",
                "reply_effective": checks[2]["status"] == "passed",
                "feedback_effective": checks[3]["status"] == "passed",
                "learning_effective": checks[4]["status"] == "passed",
                "workspace_growth_supported": checks[5]["status"] == "passed",
                "growth_intelligence": review["growth_intelligence_status"],
                "phase_completion": "Real Operations Phase completed" if passed else "Real Operations Phase needs more evidence",
                "next_stage": review["next_stage"],
                "boundary": "Local validation only; no platform API, posting, login, or account automation.",
            },
            "runtimeIntelligenceReview": review,
        }
        self.persist(report)
        return report

    def state(self) -> dict[str, Any]:
        if self.report_path.exists():
            return json.loads(self.report_path.read_text(encoding="utf-8"))
        return self.validate()

    def persist(self, report: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.review_path.write_text(json.dumps(report["runtimeIntelligenceReview"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    @staticmethod
    def _check(name: str, passed: bool, evidence: str) -> dict[str, str]:
        return {"name": name, "status": "passed" if passed else "needs_review", "evidence": evidence}

    @staticmethod
    def _workspace_growth_signal(
        daily: dict[str, Any],
        feedback: dict[str, Any],
        learning: dict[str, Any],
        failures: dict[str, Any],
    ) -> str:
        summary = daily.get("dailyOperationsSummary", {})
        feedback_summary = feedback.get("feedbackSummary", {})
        best = learning.get("learningSummary", {})
        failure_summary = failures.get("failureSummary", {})
        return (
            f"Imported {summary.get('imported_questions', 0)} questions, generated {summary.get('reply_drafts', 0)} reply drafts, "
            f"captured {feedback_summary.get('positive_feedback', 0)} positive feedback events, learned best reply "
            f"{best.get('best_answer_id', 'none')}, and identified {failure_summary.get('ignored_replies', 0)} ignored reply failure(s)."
        )


if __name__ == "__main__":
    result = RealGrowthValidationEngine().validate()
    print(json.dumps({"status": result["status"], "growth": result["realGrowthValidationSummary"]["growth_intelligence"]}, indent=2))
