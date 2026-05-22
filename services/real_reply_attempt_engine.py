"""Real reply attempt draft generation for AGOS Real Operations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.daily_question_import_engine import DailyQuestionImportEngine
from services.runtime_persistence import utc_now_iso


class RealReplyAttemptEngine:
    """Generate review-gated reply drafts from daily imported questions."""

    PLATFORMS = ["Reddit", "TikTok", "X"]

    def __init__(self, root: str | Path = "runtime/real_reply_attempts") -> None:
        self.root = Path(root)
        self.report_path = self.root / "REAL_REPLY_ATTEMPTS_REPORT.json"
        self.attempts_path = self.root / "reply_attempts.json"
        self.review_queue_path = self.root / "reply_review_queue.json"
        self.decisions_path = self.root / "reply_review_decisions.json"

    def generate_attempts(self, questions: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        daily_report = DailyQuestionImportEngine().state()
        imported_questions = questions or daily_report.get("dailyQuestions", [])
        selected = imported_questions[: min(6, len(imported_questions))]
        attempts = []
        for index, question in enumerate(selected, start=1):
            for platform in self.PLATFORMS:
                attempts.append(self._draft_attempt(question, platform, index))
        report = {
            "report_id": "REAL_REPLY_ATTEMPTS_REPORT",
            "created_at": utc_now_iso(),
            "status": "active",
            "scope": "local_draft_only_no_auto_reply",
            "supportedPlatforms": self.PLATFORMS,
            "replyAttempts": attempts,
            "replyReviewQueue": [attempt for attempt in attempts if attempt["review_status"] == "needs_human_review"],
            "replyAttemptSummary": {
                "source_questions": len(selected),
                "total_attempts": len(attempts),
                "needs_human_review": len([attempt for attempt in attempts if attempt["review_status"] == "needs_human_review"]),
                "platforms": self.PLATFORMS,
            },
        }
        self.persist(report)
        return report

    def state(self) -> dict[str, Any]:
        if self.report_path.exists():
            return json.loads(self.report_path.read_text(encoding="utf-8"))
        return self.generate_attempts()

    def persist(self, report: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.attempts_path.write_text(json.dumps(report["replyAttempts"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.review_queue_path.write_text(json.dumps(report["replyReviewQueue"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        if not self.decisions_path.exists():
            self.decisions_path.write_text("[]", encoding="utf-8")

    def approve(self, attempt_id: str) -> dict[str, Any]:
        return self._record_decision(attempt_id, "approved")

    def reject(self, attempt_id: str, reason: str) -> dict[str, Any]:
        return self._record_decision(attempt_id, "rejected", {"reject_reason": reason})

    def modify(self, attempt_id: str, modified_text: str) -> dict[str, Any]:
        return self._record_decision(attempt_id, "modified", {"human_modified_version": modified_text})

    def _record_decision(self, attempt_id: str, decision: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
        report = self.state()
        attempts = report.get("replyAttempts", [])
        target = next((attempt for attempt in attempts if attempt["reply_attempt_id"] == attempt_id), None)
        if target is None:
            raise KeyError(attempt_id)
        decision_payload = {
            "decision_id": f"decision_{len(self._load_decisions()) + 1:04d}",
            "reply_attempt_id": attempt_id,
            "question_id": target["question_id"],
            "platform": target["platform"],
            "decision": decision,
            "decided_at": utc_now_iso(),
            "details": details or {},
            "safety_boundary": "human_decision_record_only_no_auto_post",
        }
        target["review_status"] = decision
        if details:
            target.update(details)
        report["replyReviewQueue"] = [attempt for attempt in attempts if attempt["review_status"] == "needs_human_review"]
        report["replyAttemptSummary"]["needs_human_review"] = len(report["replyReviewQueue"])
        self.persist(report)
        decisions = self._load_decisions()
        decisions.append(decision_payload)
        self.decisions_path.write_text(json.dumps(decisions, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        return decision_payload

    def _load_decisions(self) -> list[dict[str, Any]]:
        if not self.decisions_path.exists():
            return []
        return json.loads(self.decisions_path.read_text(encoding="utf-8"))

    @staticmethod
    def _draft_attempt(question: dict[str, Any], platform: str, question_index: int) -> dict[str, Any]:
        attempt_id = f"{question.get('question_id', f'Q{question_index:03d}')}-{platform.lower()}-reply"
        draft_text = RealReplyAttemptEngine._draft_text(question, platform)
        return {
            "reply_attempt_id": attempt_id,
            "question_id": question.get("question_id"),
            "workspace_id": question.get("workspace_id", "JAG-LAB"),
            "source_platform": question.get("platform", "Manual"),
            "platform": platform,
            "market": question.get("market", "Japan"),
            "language": question.get("language", "en"),
            "question_text": question.get("question_text", ""),
            "canonical_pain_point": question.get("canonical_pain_point", ""),
            "reply_text": draft_text,
            "ai_reason": RealReplyAttemptEngine._reason_for(question, platform),
            "review_status": "needs_human_review",
            "status": "draft",
            "created_at": utc_now_iso(),
            "prohibited_actions": ["no_auto_reply", "no_auto_post", "no_platform_api_access"],
            "safety_boundary": "local_draft_only_requires_human_review",
        }

    @staticmethod
    def _draft_text(question: dict[str, Any], platform: str) -> str:
        text = question.get("question_text", "this question")
        if platform == "Reddit":
            return (
                f"For {text}, I would keep the route simple first: pick one main station, check transfer count, "
                "and save the route offline before leaving. This is a draft answer for human review, not an automatic reply."
            )
        if platform == "TikTok":
            return (
                f"Draft comment: If {text.lower()} is stressing you out, simplify the plan to one area, one backup route, "
                "and one offline map. Human review required before posting."
            )
        return (
            f"Draft X reply: For {text}, reduce uncertainty with one clear route, one backup, and one saved map. "
            "Needs human review before any real reply."
        )

    @staticmethod
    def _reason_for(question: dict[str, Any], platform: str) -> str:
        return (
            f"AGOS generated a {platform} draft because the imported question is review-ready and related to "
            f"{question.get('canonical_pain_point', 'a travel pain point')}. The draft stays local until approved."
        )


if __name__ == "__main__":
    result = RealReplyAttemptEngine().generate_attempts()
    print(json.dumps({"status": result["status"], "attempts": result["replyAttemptSummary"]["total_attempts"]}, indent=2))
