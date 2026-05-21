"""Workspace-scoped candidate question inbox.

The inbox accepts manually entered or imported questions only. It does not
scrape platforms or automate account behavior.
"""

from __future__ import annotations

import json
from pathlib import Path

from models.question_inbox import QuestionCandidate
from schemas.question_inbox_schema import validate_question_payload
from services.workspace_service import WorkspaceStore


class QuestionNotFoundError(KeyError):
    pass


class QuestionInboxStore:
    def __init__(self, workspace_store: WorkspaceStore | None = None) -> None:
        self.workspace_store = workspace_store or WorkspaceStore()

    def upsert(self, payload: dict) -> QuestionCandidate:
        validate_question_payload(payload)
        workspace_id = str(payload["workspace_id"])
        self.workspace_store.get(workspace_id)
        question = QuestionCandidate.from_dict(payload)
        path = self._question_file(workspace_id, question.question_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(question.to_dict(), ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        return question

    def get(self, workspace_id: str, question_id: str) -> QuestionCandidate:
        self.workspace_store.get(workspace_id)
        path = self._question_file(workspace_id, question_id)
        if not path.exists():
            raise QuestionNotFoundError(question_id)
        return QuestionCandidate.from_dict(json.loads(path.read_text(encoding="utf-8")))

    def list(self, workspace_id: str, status: str | None = None, platform: str | None = None) -> list[QuestionCandidate]:
        self.workspace_store.get(workspace_id)
        root = self._questions_dir(workspace_id)
        if not root.exists():
            return []
        items = [QuestionCandidate.from_dict(json.loads(path.read_text(encoding="utf-8"))) for path in root.glob("*.json")]
        if status:
            items = [item for item in items if item.status == status]
        if platform:
            items = [item for item in items if item.platform == platform]
        return sorted(items, key=lambda item: (-item.priority_score, item.question_id))

    def update_status(self, workspace_id: str, question_id: str, status: str) -> QuestionCandidate:
        question = self.get(workspace_id, question_id)
        payload = question.to_dict()
        payload["status"] = status
        return self.upsert(payload)

    def _questions_dir(self, workspace_id: str) -> Path:
        workspace_file = self.workspace_store._workspace_file(workspace_id)
        return workspace_file.parent / "question_inbox"

    def _question_file(self, workspace_id: str, question_id: str) -> Path:
        return self._questions_dir(workspace_id) / f"{question_id}.json"
