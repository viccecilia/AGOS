"""Workspace-scoped reply attempt tracking model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from models.workspace import utc_now_iso


@dataclass(frozen=True)
class ReplyAttempt:
    reply_attempt_id: str
    workspace_id: str
    question_id: str
    branch_id: str
    platform: str
    status: str = "draft"
    posted_at: str = ""
    liked: int = 0
    replied: int = 0
    ignored: int = 0
    saved: int = 0
    shared: int = 0
    created_at: str = field(default_factory=utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "reply_attempt_id": self.reply_attempt_id,
            "workspace_id": self.workspace_id,
            "question_id": self.question_id,
            "branch_id": self.branch_id,
            "platform": self.platform,
            "status": self.status,
            "posted_at": self.posted_at,
            "liked": self.liked,
            "replied": self.replied,
            "ignored": self.ignored,
            "saved": self.saved,
            "shared": self.shared,
            "created_at": self.created_at,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ReplyAttempt":
        return cls(
            reply_attempt_id=str(payload["reply_attempt_id"]),
            workspace_id=str(payload["workspace_id"]),
            question_id=str(payload["question_id"]),
            branch_id=str(payload["branch_id"]),
            platform=str(payload["platform"]),
            status=str(payload.get("status", "draft")),
            posted_at=str(payload.get("posted_at", "")),
            liked=int(payload.get("liked", 0)),
            replied=int(payload.get("replied", 0)),
            ignored=int(payload.get("ignored", 0)),
            saved=int(payload.get("saved", 0)),
            shared=int(payload.get("shared", 0)),
            created_at=str(payload.get("created_at", utc_now_iso())),
            metadata=dict(payload.get("metadata", {})),
        )
