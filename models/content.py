"""Workspace-scoped content draft model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from models.workspace import utc_now_iso


@dataclass(frozen=True)
class ContentDraft:
    draft_id: str
    workspace_id: str
    pain_point_id: str
    platform: str
    format: str
    title: str
    hook: str
    body: str
    tags: list[str] = field(default_factory=list)
    review_status: str = "needs_review"
    created_at: str = field(default_factory=utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "draft_id": self.draft_id,
            "workspace_id": self.workspace_id,
            "pain_point_id": self.pain_point_id,
            "platform": self.platform,
            "format": self.format,
            "title": self.title,
            "hook": self.hook,
            "body": self.body,
            "tags": list(self.tags),
            "review_status": self.review_status,
            "created_at": self.created_at,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ContentDraft":
        return cls(
            draft_id=str(payload["draft_id"]),
            workspace_id=str(payload["workspace_id"]),
            pain_point_id=str(payload["pain_point_id"]),
            platform=str(payload["platform"]),
            format=str(payload["format"]),
            title=str(payload["title"]),
            hook=str(payload["hook"]),
            body=str(payload["body"]),
            tags=list(payload.get("tags", [])),
            review_status=str(payload.get("review_status", "needs_review")),
            created_at=str(payload.get("created_at", utc_now_iso())),
            metadata=dict(payload.get("metadata", {})),
        )
