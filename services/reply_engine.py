"""Workspace-scoped reply draft engine."""

from __future__ import annotations

import json
import re
from pathlib import Path

from models.reply import ReplyDraft
from schemas.reply_schema import validate_reply_payload
from services.knowledge_service import KnowledgeBaseStore
from services.workspace_service import WorkspaceStore


HIGH_RISK_PATTERNS = {
    "hard_sell": re.compile(r"\b(buy now|limited offer|guaranteed|click my link)\b", re.I),
    "impersonation": re.compile(r"\bI personally used|as a local official|we guarantee\b", re.I),
}


class ReplyDraftStore:
    def __init__(self, workspace_store: WorkspaceStore | None = None, knowledge_store: KnowledgeBaseStore | None = None) -> None:
        self.workspace_store = workspace_store or WorkspaceStore()
        self.knowledge_store = knowledge_store or KnowledgeBaseStore(self.workspace_store)

    def generate(self, workspace_id: str, source_platform: str, source_text: str, reply_id: str) -> ReplyDraft:
        self.workspace_store.get(workspace_id)
        knowledge = self.knowledge_store.get(workspace_id)
        draft_text = (
            f"{knowledge.brand_voice}\n"
            f"Thanks for raising this. A practical way to approach it is to first clarify the exact situation, "
            f"then choose the simplest next step. For your note: \"{source_text}\". "
            "This is a draft for human review, not an automatic reply."
        )
        risk_level, reasons = self.assess_risk(draft_text)
        return self.upsert(
            {
                "reply_id": reply_id,
                "workspace_id": workspace_id,
                "source_platform": source_platform,
                "source_text": source_text,
                "draft_text": draft_text,
                "review_status": "needs_review",
                "risk_level": risk_level,
                "risk_reasons": reasons,
            }
        )

    def upsert(self, payload: dict) -> ReplyDraft:
        validate_reply_payload(payload)
        self.workspace_store.get(str(payload["workspace_id"]))
        reply = ReplyDraft.from_dict(payload)
        path = self._reply_file(reply.workspace_id, reply.reply_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(reply.to_dict(), ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        return reply

    def list(self, workspace_id: str) -> list[ReplyDraft]:
        self.workspace_store.get(workspace_id)
        root = self._replies_dir(workspace_id)
        if not root.exists():
            return []
        return sorted(
            [ReplyDraft.from_dict(json.loads(path.read_text(encoding="utf-8"))) for path in root.glob("*.json")],
            key=lambda item: item.reply_id,
        )

    @staticmethod
    def assess_risk(text: str) -> tuple[str, list[str]]:
        reasons = [name for name, pattern in HIGH_RISK_PATTERNS.items() if pattern.search(text)]
        return ("blocked" if reasons else "normal", reasons)

    def _replies_dir(self, workspace_id: str) -> Path:
        workspace_file = self.workspace_store._workspace_file(workspace_id)
        return workspace_file.parent / "reply_drafts"

    def _reply_file(self, workspace_id: str, reply_id: str) -> Path:
        return self._replies_dir(workspace_id) / f"{reply_id}.json"
