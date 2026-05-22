"""Failure analysis for AGOS Real Operations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.best_answer_learning_engine import BestAnswerLearningEngine
from services.real_feedback_capture_engine import RealFeedbackCaptureEngine
from services.runtime_persistence import utc_now_iso


class FailureAnalysisEngine:
    """Explain why ignored content, replies, hooks, and strategies failed."""

    def __init__(self, root: str | Path = "runtime/failure_analysis") -> None:
        self.root = Path(root)
        self.report_path = self.root / "FAILURE_ANALYSIS_REPORT.json"
        self.failures_path = self.root / "failure_items.json"
        self.timeline_path = self.root / "failure_timeline.json"

    def analyze(self) -> dict[str, Any]:
        feedback = RealFeedbackCaptureEngine().state()
        learning = BestAnswerLearningEngine().state()
        ignored = [event for event in feedback.get("feedbackEvents", []) if event.get("has_negative_feedback")]
        failed_answers = learning.get("bestAnswerLearning", {}).get("failedAnswers", [])
        failed_hooks = learning.get("bestAnswerLearning", {}).get("failedHooks", [])
        failed_strategies = learning.get("bestAnswerLearning", {}).get("failedStrategies", [])
        failure_items = [self._failure_from_event(event) for event in ignored]
        failure_items.extend(self._failure_from_failed_answer(item) for item in failed_answers)
        failed_hook_items = [self._failure_from_failed_hook(item) for item in failed_hooks]
        failed_strategy_items = [self._failure_from_failed_strategy(item) for item in failed_strategies]
        failure_items.extend(failed_hook_items)
        failure_items.extend(failed_strategy_items)
        report = {
            "report_id": "FAILURE_ANALYSIS_REPORT",
            "created_at": utc_now_iso(),
            "status": "active",
            "scope": "local_failure_analysis_only_no_platform_api",
            "ignoredContent": ignored,
            "ignoredReplies": ignored,
            "failedHooks": failed_hooks,
            "failedStrategies": failed_strategies,
            "failureItems": failure_items,
            "failureTimeline": self._timeline(failure_items),
            "failureSummary": {
                "ignored_content": len(ignored),
                "ignored_replies": len(ignored),
                "failed_hooks": len(failed_hooks),
                "failed_strategies": len(failed_strategies),
                "top_failure_reason": failure_items[0]["why_failed"] if failure_items else "none",
                "can_explain_failure": bool(failure_items),
            },
        }
        self.persist(report)
        return report

    def state(self) -> dict[str, Any]:
        if self.report_path.exists():
            return json.loads(self.report_path.read_text(encoding="utf-8"))
        return self.analyze()

    def persist(self, report: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.failures_path.write_text(json.dumps(report["failureItems"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.timeline_path.write_text(json.dumps(report["failureTimeline"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    @staticmethod
    def _failure_from_event(event: dict[str, Any]) -> dict[str, Any]:
        question = event.get("question_text", "")
        reply = event.get("reply_text", "")
        why = FailureAnalysisEngine._why_failed(question, reply, event.get("platform", "unknown"))
        return {
            "failure_id": "failure_" + str(event.get("feedback_id", "unknown")),
            "source": "feedback_capture",
            "reply_attempt_id": event.get("reply_attempt_id"),
            "platform": event.get("platform", "unknown"),
            "question_text": question,
            "reply_text": reply,
            "why_failed": why,
            "failure_type": "ignored_reply",
            "fix_recommendation": FailureAnalysisEngine._fix_for(why),
            "status": "analyzed",
        }

    @staticmethod
    def _failure_from_failed_answer(item: dict[str, Any]) -> dict[str, Any]:
        why = "Answer produced no positive feedback and should not be learned as a best pattern."
        return {
            "failure_id": "failure_learning_" + str(item.get("reply_attempt_id", "unknown")),
            "source": "best_answer_learning",
            "reply_attempt_id": item.get("reply_attempt_id"),
            "platform": item.get("platform", "unknown"),
            "question_text": item.get("question_text", ""),
            "reply_text": item.get("reply_text", ""),
            "why_failed": why,
            "failure_type": "failed_answer",
            "fix_recommendation": "Make the answer more specific, reduce generic phrasing, and require human review before reuse.",
            "status": "analyzed",
        }

    @staticmethod
    def _failure_from_failed_hook(item: str | dict[str, Any]) -> dict[str, Any]:
        hook = item.get("hook", "") if isinstance(item, dict) else str(item)
        why = "Hook failed because it did not make the practical travel payoff visible fast enough."
        return {
            "failure_id": "failure_hook_" + str(abs(hash(hook)) % 100000),
            "source": "best_answer_learning",
            "platform": item.get("platform", "unknown") if isinstance(item, dict) else "unknown",
            "hook": hook,
            "why_failed": why,
            "failure_type": "failed_hook",
            "fix_recommendation": "Name the concrete pain point in the first phrase and promise one useful next step.",
            "status": "analyzed",
        }

    @staticmethod
    def _failure_from_failed_strategy(item: str | dict[str, Any]) -> dict[str, Any]:
        strategy = item.get("strategy", "") if isinstance(item, dict) else str(item)
        why = "Strategy failed because it produced weak feedback or could not be tied to a clear user pain signal."
        return {
            "failure_id": "failure_strategy_" + str(abs(hash(strategy)) % 100000),
            "source": "best_answer_learning",
            "platform": item.get("platform", "unknown") if isinstance(item, dict) else "unknown",
            "strategy": strategy,
            "why_failed": why,
            "failure_type": "failed_strategy",
            "fix_recommendation": "Retest with a narrower audience, clearer pain point, and explicit human review.",
            "status": "analyzed",
        }

    @staticmethod
    def _why_failed(question: str, reply: str, platform: str) -> str:
        lower_reply = reply.lower()
        if len(reply) < 80:
            return "Reply was too short to create useful confidence."
        if platform == "X" and len(reply) > 220:
            return "X reply was too dense for the platform and likely lost attention."
        if "try" in lower_reply and "specific" not in lower_reply and "route" not in lower_reply:
            return "Reply gave generic advice without enough concrete next steps."
        if "station" in question.lower() and "gate" not in lower_reply and "route" not in lower_reply:
            return "Transit answer did not provide a concrete station route or gate-level detail."
        return "Reply did not produce visible engagement in the feedback window."

    @staticmethod
    def _fix_for(reason: str) -> str:
        if "too short" in reason:
            return "Add 2-3 concrete steps and one example."
        if "too dense" in reason:
            return "Compress to one insight and one practical action."
        if "generic" in reason:
            return "Replace generic advice with platform-specific, pain-specific instructions."
        if "station" in reason:
            return "Add station names, transfer count, and a simple backup route."
        return "Try a clearer hook and stronger practical detail."

    @staticmethod
    def _timeline(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "time": utc_now_iso(),
                "type": item["failure_type"],
                "reply_attempt_id": item.get("reply_attempt_id"),
                "platform": item.get("platform"),
                "why_failed": item["why_failed"],
                "fix_recommendation": item["fix_recommendation"],
                "status": item["status"],
            }
            for item in items
        ]


if __name__ == "__main__":
    result = FailureAnalysisEngine().analyze()
    print(json.dumps({"status": result["status"], "failures": len(result["failureItems"])}, indent=2))
