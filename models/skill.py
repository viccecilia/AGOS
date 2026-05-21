"""Skill marketplace model."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SkillDefinition:
    skill_id: str
    name: str
    category: str
    required_plan: str
    enabled_by_default: bool = False
    capabilities: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "category": self.category,
            "required_plan": self.required_plan,
            "enabled_by_default": self.enabled_by_default,
            "capabilities": list(self.capabilities),
        }
