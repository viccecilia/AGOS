"""Customer knowledge base model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from models.workspace import utc_now_iso


@dataclass(frozen=True)
class KnowledgeBase:
    workspace_id: str
    brand_voice: str
    product_facts: list[dict[str, str]] = field(default_factory=list)
    faqs: list[dict[str, str]] = field(default_factory=list)
    industry_notes: list[str] = field(default_factory=list)
    content_templates: list[dict[str, str]] = field(default_factory=list)
    updated_at: str = field(default_factory=utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "workspace_id": self.workspace_id,
            "brand_voice": self.brand_voice,
            "product_facts": list(self.product_facts),
            "faqs": list(self.faqs),
            "industry_notes": list(self.industry_notes),
            "content_templates": list(self.content_templates),
            "updated_at": self.updated_at,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "KnowledgeBase":
        return cls(
            workspace_id=str(payload["workspace_id"]),
            brand_voice=str(payload["brand_voice"]),
            product_facts=list(payload.get("product_facts", [])),
            faqs=list(payload.get("faqs", [])),
            industry_notes=list(payload.get("industry_notes", [])),
            content_templates=list(payload.get("content_templates", [])),
            updated_at=str(payload.get("updated_at", utc_now_iso())),
            metadata=dict(payload.get("metadata", {})),
        )
