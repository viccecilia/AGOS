"""Skill marketplace permission engine."""

from __future__ import annotations

from models.skill import SkillDefinition
from schemas.skill_schema import PLAN_ORDER, validate_skill_payload


class SkillPermissionError(PermissionError):
    pass


DEFAULT_SKILLS = [
    {"skill_id": "seo_skill", "name": "SEO Skill", "category": "growth", "required_plan": "starter", "enabled_by_default": True, "capabilities": ["seo_article"]},
    {"skill_id": "tiktok_skill", "name": "TikTok Skill", "category": "short_video", "required_plan": "growth", "enabled_by_default": False, "capabilities": ["short_video"]},
    {"skill_id": "reddit_skill", "name": "Reddit Skill", "category": "community", "required_plan": "growth", "enabled_by_default": False, "capabilities": ["reply_seed"]},
    {"skill_id": "premium_ai_pack", "name": "Premium AI Pack", "category": "premium", "required_plan": "premium", "enabled_by_default": False, "capabilities": ["report_summary", "content_draft"]},
]


class SkillMarketplace:
    def __init__(self, skills: list[dict] | None = None) -> None:
        self.skills = {}
        for payload in skills or DEFAULT_SKILLS:
            validate_skill_payload(payload)
            skill = SkillDefinition(**payload)
            self.skills[skill.skill_id] = skill

    def available_for_plan(self, plan: str) -> list[SkillDefinition]:
        return [skill for skill in self.skills.values() if PLAN_ORDER[plan] >= PLAN_ORDER[skill.required_plan]]

    def can_enable(self, plan: str, skill_id: str) -> bool:
        skill = self.skills[skill_id]
        return PLAN_ORDER[plan] >= PLAN_ORDER[skill.required_plan]

    def require_enabled(self, plan: str, skill_id: str, enabled_skill_ids: set[str]) -> SkillDefinition:
        if not self.can_enable(plan, skill_id):
            raise SkillPermissionError(f"Plan {plan} cannot enable {skill_id}")
        if skill_id not in enabled_skill_ids:
            raise SkillPermissionError(f"Skill {skill_id} is disabled")
        return self.skills[skill_id]
