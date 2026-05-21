"""Workspace-scoped content draft generator.

This MVP creates reviewable drafts from local knowledge and pain point data. It
does not publish content or call external AI providers.
"""

from __future__ import annotations

import json
from pathlib import Path

from models.content import ContentDraft
from schemas.content_schema import validate_content_payload
from services.knowledge_service import KnowledgeBaseStore
from services.pain_point_engine import PainPointStore
from services.workspace_service import WorkspaceStore


PLATFORM_FORMAT = {
    "tiktok": "short_video",
    "instagram": "post",
    "reddit": "reply_seed",
    "youtube": "youtube_outline",
    "seo": "seo_article",
}


class ContentDraftNotFoundError(KeyError):
    pass


class ContentDraftStore:
    def __init__(
        self,
        workspace_store: WorkspaceStore | None = None,
        knowledge_store: KnowledgeBaseStore | None = None,
        pain_point_store: PainPointStore | None = None,
    ) -> None:
        self.workspace_store = workspace_store or WorkspaceStore()
        self.knowledge_store = knowledge_store or KnowledgeBaseStore(self.workspace_store)
        self.pain_point_store = pain_point_store or PainPointStore(self.workspace_store)

    def generate_for_top_pain_points(self, workspace_id: str, platforms: list[str], limit: int = 1) -> list[ContentDraft]:
        self.workspace_store.get(workspace_id)
        knowledge = self.knowledge_store.get(workspace_id)
        pain_points = self.pain_point_store.top(workspace_id, limit=limit)
        drafts: list[ContentDraft] = []
        for pain_point in pain_points:
            for platform in platforms:
                drafts.append(self.upsert(self._build_draft(workspace_id, platform, pain_point, knowledge.brand_voice)))
        return drafts

    def upsert(self, payload: dict) -> ContentDraft:
        validate_content_payload(payload)
        self.workspace_store.get(str(payload["workspace_id"]))
        draft = ContentDraft.from_dict(payload)
        path = self._draft_file(draft.workspace_id, draft.draft_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(draft.to_dict(), ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return draft

    def list(self, workspace_id: str, platform: str | None = None) -> list[ContentDraft]:
        self.workspace_store.get(workspace_id)
        root = self._drafts_dir(workspace_id)
        if not root.exists():
            return []
        drafts = [ContentDraft.from_dict(json.loads(path.read_text(encoding="utf-8"))) for path in root.glob("*.json")]
        if platform:
            drafts = [item for item in drafts if item.platform == platform]
        return sorted(drafts, key=lambda item: item.draft_id)

    def _build_draft(self, workspace_id: str, platform: str, pain_point, brand_voice: str) -> dict:
        content_format = PLATFORM_FORMAT.get(platform, "post")
        draft_id = f"{pain_point.pain_point_id}_{platform}"
        title = f"{pain_point.title} ({platform})"
        hook = f"If {pain_point.audience} struggle with {pain_point.category}, start here."
        body = (
            f"Brand voice: {brand_voice}\n"
            f"Pain point: {pain_point.title}\n"
            f"Evidence: {pain_point.evidence}\n"
            f"Platform angle: adapt this into a {content_format} for {platform}.\n"
            "Review required before any publication."
        )
        return {
            "draft_id": draft_id,
            "workspace_id": workspace_id,
            "pain_point_id": pain_point.pain_point_id,
            "platform": platform,
            "format": content_format,
            "title": title,
            "hook": hook,
            "body": body,
            "tags": pain_point.tags + [platform, content_format],
            "review_status": "needs_review",
            "metadata": {"source_priority_score": pain_point.priority_score},
        }

    def _drafts_dir(self, workspace_id: str) -> Path:
        workspace_file = self.workspace_store._workspace_file(workspace_id)
        return workspace_file.parent / "content_drafts"

    def _draft_file(self, workspace_id: str, draft_id: str) -> Path:
        return self._drafts_dir(workspace_id) / f"{draft_id}.json"
