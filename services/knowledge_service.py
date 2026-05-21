"""Workspace-scoped customer knowledge base service."""

from __future__ import annotations

import json
from pathlib import Path

from models.knowledge import KnowledgeBase
from models.workspace import utc_now_iso
from schemas.knowledge_schema import validate_knowledge_payload
from services.workspace_service import WorkspaceStore


class KnowledgeBaseNotFoundError(KeyError):
    pass


class KnowledgeBaseStore:
    def __init__(self, workspace_store: WorkspaceStore | None = None) -> None:
        self.workspace_store = workspace_store or WorkspaceStore()

    def upsert(self, payload: dict) -> KnowledgeBase:
        validate_knowledge_payload(payload)
        workspace_id = str(payload["workspace_id"])
        self.workspace_store.get(workspace_id)
        knowledge = KnowledgeBase.from_dict({**payload, "updated_at": utc_now_iso()})
        path = self._knowledge_file(workspace_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(knowledge.to_dict(), ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return knowledge

    def get(self, workspace_id: str) -> KnowledgeBase:
        self.workspace_store.get(workspace_id)
        path = self._knowledge_file(workspace_id)
        if not path.exists():
            raise KnowledgeBaseNotFoundError(workspace_id)
        return KnowledgeBase.from_dict(json.loads(path.read_text(encoding="utf-8")))

    def exists(self, workspace_id: str) -> bool:
        return self._knowledge_file(workspace_id).exists()

    def _knowledge_file(self, workspace_id: str) -> Path:
        workspace_file = self.workspace_store._workspace_file(workspace_id)
        return workspace_file.parent / "knowledge_base.json"
