"""Workspace domain model.

A workspace is the isolation boundary for one customer/product growth system.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class Workspace:
    workspace_id: str
    name: str
    owner: str
    product_name: str
    industry: str
    target_markets: list[str] = field(default_factory=list)
    status: str = "draft"
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "workspace_id": self.workspace_id,
            "name": self.name,
            "owner": self.owner,
            "product_name": self.product_name,
            "industry": self.industry,
            "target_markets": list(self.target_markets),
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Workspace":
        return cls(
            workspace_id=str(payload["workspace_id"]),
            name=str(payload["name"]),
            owner=str(payload["owner"]),
            product_name=str(payload["product_name"]),
            industry=str(payload["industry"]),
            target_markets=list(payload.get("target_markets", [])),
            status=str(payload.get("status", "draft")),
            created_at=str(payload.get("created_at", utc_now_iso())),
            updated_at=str(payload.get("updated_at", utc_now_iso())),
            metadata=dict(payload.get("metadata", {})),
        )
