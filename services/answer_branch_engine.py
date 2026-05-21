"""Workspace-scoped answer branch service."""

from __future__ import annotations

import json
from pathlib import Path

from models.answer_branch import AnswerBranch
from schemas.answer_branch_schema import validate_answer_branch_payload
from services.question_inbox_engine import QuestionInboxStore
from services.workspace_service import WorkspaceStore


class AnswerBranchNotFoundError(KeyError):
    pass


class AnswerBranchStore:
    def __init__(
        self,
        workspace_store: WorkspaceStore | None = None,
        question_store: QuestionInboxStore | None = None,
    ) -> None:
        self.workspace_store = workspace_store or WorkspaceStore()
        self.question_store = question_store or QuestionInboxStore(self.workspace_store)

    def upsert(self, payload: dict) -> AnswerBranch:
        validate_answer_branch_payload(payload)
        workspace_id = str(payload["workspace_id"])
        self.workspace_store.get(workspace_id)
        self.question_store.get(workspace_id, str(payload["question_id"]))
        branch = AnswerBranch.from_dict(payload)
        path = self._branch_file(workspace_id, branch.branch_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(branch.to_dict(), ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        return branch

    def get(self, workspace_id: str, branch_id: str) -> AnswerBranch:
        self.workspace_store.get(workspace_id)
        path = self._branch_file(workspace_id, branch_id)
        if not path.exists():
            raise AnswerBranchNotFoundError(branch_id)
        return AnswerBranch.from_dict(json.loads(path.read_text(encoding="utf-8")))

    def list(self, workspace_id: str, question_id: str | None = None, platform: str | None = None) -> list[AnswerBranch]:
        self.workspace_store.get(workspace_id)
        root = self._branches_dir(workspace_id)
        if not root.exists():
            return []
        branches = [AnswerBranch.from_dict(json.loads(path.read_text(encoding="utf-8"))) for path in root.glob("*.json")]
        if question_id:
            branches = [item for item in branches if item.question_id == question_id]
        if platform:
            branches = [item for item in branches if item.platform == platform]
        return sorted(branches, key=lambda item: item.branch_id)

    def approve(self, workspace_id: str, branch_id: str) -> AnswerBranch:
        branch = self.get(workspace_id, branch_id)
        payload = branch.to_dict()
        payload["review_status"] = "approved"
        return self.upsert(payload)

    def mark_best(self, workspace_id: str, branch_id: str) -> AnswerBranch:
        selected = self.get(workspace_id, branch_id)
        for branch in self.list(workspace_id, question_id=selected.question_id):
            payload = branch.to_dict()
            payload["best_answer"] = branch.branch_id == branch_id
            self.upsert(payload)
        return self.get(workspace_id, branch_id)

    def _branches_dir(self, workspace_id: str) -> Path:
        workspace_file = self.workspace_store._workspace_file(workspace_id)
        return workspace_file.parent / "answer_branches"

    def _branch_file(self, workspace_id: str, branch_id: str) -> Path:
        return self._branches_dir(workspace_id) / f"{branch_id}.json"
