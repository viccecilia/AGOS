"""AI provider configuration model."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class AIProviderConfig:
    provider_id: str
    provider_type: str
    display_name: str
    capabilities: list[str] = field(default_factory=list)
    monthly_quota: int = 0
    enabled: bool = True

    def to_dict(self) -> dict:
        return {
            "provider_id": self.provider_id,
            "provider_type": self.provider_type,
            "display_name": self.display_name,
            "capabilities": list(self.capabilities),
            "monthly_quota": self.monthly_quota,
            "enabled": self.enabled,
        }
