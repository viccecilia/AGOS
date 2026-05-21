"""Workspace-scoped report model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from models.workspace import utc_now_iso


@dataclass(frozen=True)
class GrowthReport:
    report_id: str
    workspace_id: str
    report_type: str
    title: str
    summary: str
    metrics: dict[str, Any]
    recommendations: list[str]
    created_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "workspace_id": self.workspace_id,
            "report_type": self.report_type,
            "title": self.title,
            "summary": self.summary,
            "metrics": dict(self.metrics),
            "recommendations": list(self.recommendations),
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "GrowthReport":
        return cls(
            report_id=str(payload["report_id"]),
            workspace_id=str(payload["workspace_id"]),
            report_type=str(payload["report_type"]),
            title=str(payload["title"]),
            summary=str(payload["summary"]),
            metrics=dict(payload.get("metrics", {})),
            recommendations=list(payload.get("recommendations", [])),
            created_at=str(payload.get("created_at", utc_now_iso())),
        )
