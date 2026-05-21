"""Workspace-scoped answer branch model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from models.workspace import utc_now_iso


@dataclass(frozen=True)
class AnswerBranch:
    branch_id: str
    workspace_id: str
    question_id: str
    platform: str
    tone: str
    reply_text: str
    soft_cta: str
    engagement_score: float = 0
    ignore_score: float = 0
    save_score: float = 0
    best_answer: bool = False
    review_status: str = "needs_review"
    created_at: str = field(default_factory=utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "branch_id": self.branch_id,
            "workspace_id": self.workspace_id,
            "question_id": self.question_id,
            "platform": self.platform,
            "tone": self.tone,
            "reply_text": self.reply_text,
            "soft_cta": self.soft_cta,
            "engagement_score": self.engagement_score,
            "ignore_score": self.ignore_score,
            "save_score": self.save_score,
            "best_answer": self.best_answer,
            "review_status": self.review_status,
            "created_at": self.created_at,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "AnswerBranch":
        return cls(
            branch_id=str(payload["branch_id"]),
            workspace_id=str(payload["workspace_id"]),
            question_id=str(payload["question_id"]),
            platform=str(payload["platform"]),
            tone=str(payload["tone"]),
            reply_text=str(payload["reply_text"]),
            soft_cta=str(payload.get("soft_cta", "")),
            engagement_score=float(payload.get("engagement_score", 0)),
            ignore_score=float(payload.get("ignore_score", 0)),
            save_score=float(payload.get("save_score", 0)),
            best_answer=bool(payload.get("best_answer", False)),
            review_status=str(payload.get("review_status", "needs_review")),
            created_at=str(payload.get("created_at", utc_now_iso())),
            metadata=dict(payload.get("metadata", {})),
        )
