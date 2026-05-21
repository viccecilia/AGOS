"""Workspace-scoped learning event model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from models.workspace import utc_now_iso


@dataclass(frozen=True)
class LearningEvent:
    event_id: str
    workspace_id: str
    target_type: str
    target_id: str
    signal: str
    weight: float
    note: str = ""
    created_at: str = field(default_factory=utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "workspace_id": self.workspace_id,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "signal": self.signal,
            "weight": self.weight,
            "note": self.note,
            "created_at": self.created_at,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "LearningEvent":
        return cls(
            event_id=str(payload["event_id"]),
            workspace_id=str(payload["workspace_id"]),
            target_type=str(payload["target_type"]),
            target_id=str(payload["target_id"]),
            signal=str(payload["signal"]),
            weight=float(payload["weight"]),
            note=str(payload.get("note", "")),
            created_at=str(payload.get("created_at", utc_now_iso())),
            metadata=dict(payload.get("metadata", {})),
        )
