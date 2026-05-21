"""Workspace-scoped official account matrix model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from models.workspace import utc_now_iso


@dataclass(frozen=True)
class AccountProfile:
    account_id: str
    workspace_id: str
    platform: str
    handle: str
    display_name: str
    status: str = "draft"
    content_strategy: str = ""
    risk_status: str = "normal"
    notes: str = ""
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "account_id": self.account_id,
            "workspace_id": self.workspace_id,
            "platform": self.platform,
            "handle": self.handle,
            "display_name": self.display_name,
            "status": self.status,
            "content_strategy": self.content_strategy,
            "risk_status": self.risk_status,
            "notes": self.notes,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "AccountProfile":
        return cls(
            account_id=str(payload["account_id"]),
            workspace_id=str(payload["workspace_id"]),
            platform=str(payload["platform"]),
            handle=str(payload["handle"]),
            display_name=str(payload["display_name"]),
            status=str(payload.get("status", "draft")),
            content_strategy=str(payload.get("content_strategy", "")),
            risk_status=str(payload.get("risk_status", "normal")),
            notes=str(payload.get("notes", "")),
            created_at=str(payload.get("created_at", utc_now_iso())),
            updated_at=str(payload.get("updated_at", utc_now_iso())),
            metadata=dict(payload.get("metadata", {})),
        )
