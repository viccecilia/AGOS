"""Workspace-scoped candidate question model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from models.workspace import utc_now_iso


@dataclass(frozen=True)
class QuestionCandidate:
    question_id: str
    workspace_id: str
    platform: str
    language: str
    market: str
    audience: str
    source_url: str
    question_text: str
    pain_points: list[str] = field(default_factory=list)
    emotion_tags: list[str] = field(default_factory=list)
    status: str = "new"
    priority_score: float = 0
    created_at: str = field(default_factory=utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "question_id": self.question_id,
            "workspace_id": self.workspace_id,
            "platform": self.platform,
            "language": self.language,
            "market": self.market,
            "audience": self.audience,
            "source_url": self.source_url,
            "question_text": self.question_text,
            "pain_points": list(self.pain_points),
            "emotion_tags": list(self.emotion_tags),
            "status": self.status,
            "priority_score": self.priority_score,
            "created_at": self.created_at,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "QuestionCandidate":
        return cls(
            question_id=str(payload["question_id"]),
            workspace_id=str(payload["workspace_id"]),
            platform=str(payload["platform"]),
            language=str(payload["language"]),
            market=str(payload["market"]),
            audience=str(payload["audience"]),
            source_url=str(payload.get("source_url", "")),
            question_text=str(payload["question_text"]),
            pain_points=list(payload.get("pain_points", [])),
            emotion_tags=list(payload.get("emotion_tags", [])),
            status=str(payload.get("status", "new")),
            priority_score=float(payload.get("priority_score", 0)),
            created_at=str(payload.get("created_at", utc_now_iso())),
            metadata=dict(payload.get("metadata", {})),
        )
