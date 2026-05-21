"""Workspace-scoped reply draft model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from models.workspace import utc_now_iso


@dataclass(frozen=True)
class ReplyDraft:
    reply_id: str
    workspace_id: str
    source_platform: str
    source_text: str
    draft_text: str
    review_status: str = "needs_review"
    risk_level: str = "normal"
    risk_reasons: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "reply_id": self.reply_id,
            "workspace_id": self.workspace_id,
            "source_platform": self.source_platform,
            "source_text": self.source_text,
            "draft_text": self.draft_text,
            "review_status": self.review_status,
            "risk_level": self.risk_level,
            "risk_reasons": list(self.risk_reasons),
            "created_at": self.created_at,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ReplyDraft":
        return cls(
            reply_id=str(payload["reply_id"]),
            workspace_id=str(payload["workspace_id"]),
            source_platform=str(payload["source_platform"]),
            source_text=str(payload["source_text"]),
            draft_text=str(payload["draft_text"]),
            review_status=str(payload.get("review_status", "needs_review")),
            risk_level=str(payload.get("risk_level", "normal")),
            risk_reasons=list(payload.get("risk_reasons", [])),
            created_at=str(payload.get("created_at", utc_now_iso())),
            metadata=dict(payload.get("metadata", {})),
        )
