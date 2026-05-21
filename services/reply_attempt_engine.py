"""Workspace-scoped reply attempt tracking service."""

from __future__ import annotations

import json
from pathlib import Path

from models.reply_attempt import ReplyAttempt
from schemas.reply_attempt_schema import validate_reply_attempt_payload
from services.answer_branch_engine import AnswerBranchStore
from services.question_inbox_engine import QuestionInboxStore
from services.workspace_service import WorkspaceStore


class ReplyAttemptNotFoundError(KeyError):
    pass


class ReplyAttemptStore:
    def __init__(
        self,
        workspace_store: WorkspaceStore | None = None,
        question_store: QuestionInboxStore | None = None,
        branch_store: AnswerBranchStore | None = None,
    ) -> None:
        self.workspace_store = workspace_store or WorkspaceStore()
        self.question_store = question_store or QuestionInboxStore(self.workspace_store)
        self.branch_store = branch_store or AnswerBranchStore(self.workspace_store, self.question_store)

    def upsert(self, payload: dict) -> ReplyAttempt:
        validate_reply_attempt_payload(payload)
        workspace_id = str(payload["workspace_id"])
        question_id = str(payload["question_id"])
        branch_id = str(payload["branch_id"])
        self.workspace_store.get(workspace_id)
        self.question_store.get(workspace_id, question_id)
        branch = self.branch_store.get(workspace_id, branch_id)
        if branch.question_id != question_id:
            raise ValueError("reply attempt branch does not belong to question")
        attempt = ReplyAttempt.from_dict(payload)
        path = self._attempt_file(workspace_id, attempt.reply_attempt_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(attempt.to_dict(), ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        return attempt

    def get(self, workspace_id: str, reply_attempt_id: str) -> ReplyAttempt:
        self.workspace_store.get(workspace_id)
        path = self._attempt_file(workspace_id, reply_attempt_id)
        if not path.exists():
            raise ReplyAttemptNotFoundError(reply_attempt_id)
        return ReplyAttempt.from_dict(json.loads(path.read_text(encoding="utf-8")))

    def list(self, workspace_id: str, status: str | None = None) -> list[ReplyAttempt]:
        self.workspace_store.get(workspace_id)
        root = self._attempts_dir(workspace_id)
        if not root.exists():
            return []
        attempts = [ReplyAttempt.from_dict(json.loads(path.read_text(encoding="utf-8"))) for path in root.glob("*.json")]
        if status:
            attempts = [item for item in attempts if item.status == status]
        return sorted(attempts, key=lambda item: item.reply_attempt_id)

    def approve(self, workspace_id: str, reply_attempt_id: str) -> ReplyAttempt:
        attempt = self.get(workspace_id, reply_attempt_id)
        branch = self.branch_store.get(workspace_id, attempt.branch_id)
        if branch.review_status != "approved":
            raise ValueError("reply attempt cannot be approved until answer branch is approved")
        payload = attempt.to_dict()
        payload["status"] = "approved"
        return self.upsert(payload)

    def record_feedback(
        self,
        workspace_id: str,
        reply_attempt_id: str,
        *,
        liked: int = 0,
        replied: int = 0,
        ignored: int = 0,
        saved: int = 0,
        shared: int = 0,
    ) -> ReplyAttempt:
        attempt = self.get(workspace_id, reply_attempt_id)
        payload = attempt.to_dict()
        payload.update({"liked": liked, "replied": replied, "ignored": ignored, "saved": saved, "shared": shared})
        if replied + liked + saved + shared >= 3:
            payload["status"] = "high_engagement"
        elif ignored > 0 and replied + liked + saved + shared == 0:
            payload["status"] = "ignored"
        return self.upsert(payload)

    def _attempts_dir(self, workspace_id: str) -> Path:
        workspace_file = self.workspace_store._workspace_file(workspace_id)
        return workspace_file.parent / "reply_attempts"

    def _attempt_file(self, workspace_id: str, reply_attempt_id: str) -> Path:
        return self._attempts_dir(workspace_id) / f"{reply_attempt_id}.json"
