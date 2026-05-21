"""Workspace-scoped pain point radar model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from models.workspace import utc_now_iso


@dataclass(frozen=True)
class PainPoint:
    pain_point_id: str
    workspace_id: str
    source: str
    platform: str
    market: str
    audience: str
    category: str
    title: str
    evidence: str
    trend_score: float
    urgency_score: float
    value_score: float
    tags: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def priority_score(self) -> float:
        return round((self.trend_score * 0.45) + (self.urgency_score * 0.30) + (self.value_score * 0.25), 4)

    def to_dict(self) -> dict[str, Any]:
        return {
            "pain_point_id": self.pain_point_id,
            "workspace_id": self.workspace_id,
            "source": self.source,
            "platform": self.platform,
            "market": self.market,
            "audience": self.audience,
            "category": self.category,
            "title": self.title,
            "evidence": self.evidence,
            "trend_score": self.trend_score,
            "urgency_score": self.urgency_score,
            "value_score": self.value_score,
            "priority_score": self.priority_score,
            "tags": list(self.tags),
            "created_at": self.created_at,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "PainPoint":
        return cls(
            pain_point_id=str(payload["pain_point_id"]),
            workspace_id=str(payload["workspace_id"]),
            source=str(payload["source"]),
            platform=str(payload["platform"]),
            market=str(payload["market"]),
            audience=str(payload["audience"]),
            category=str(payload["category"]),
            title=str(payload["title"]),
            evidence=str(payload["evidence"]),
            trend_score=float(payload["trend_score"]),
            urgency_score=float(payload["urgency_score"]),
            value_score=float(payload["value_score"]),
            tags=list(payload.get("tags", [])),
            created_at=str(payload.get("created_at", utc_now_iso())),
            metadata=dict(payload.get("metadata", {})),
        )
