"""Skill marketplace schema validation."""

from __future__ import annotations

import re
from typing import Any


SKILL_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{2,79}$")
PLANS = {"free", "starter", "growth", "premium", "enterprise"}
PLAN_ORDER = {name: index for index, name in enumerate(["free", "starter", "growth", "premium", "enterprise"])}


class SkillValidationError(ValueError):
    pass


def validate_skill_payload(payload: dict[str, Any]) -> None:
    if not SKILL_ID_PATTERN.fullmatch(str(payload.get("skill_id", ""))):
        raise SkillValidationError("invalid skill_id")
    for field in ["name", "category"]:
        if not str(payload.get(field, "")).strip():
            raise SkillValidationError(f"{field} is required")
    if str(payload.get("required_plan", "")) not in PLANS:
        raise SkillValidationError("invalid required_plan")
    capabilities = payload.get("capabilities", [])
    if not isinstance(capabilities, list) or not all(isinstance(item, str) and item.strip() for item in capabilities):
        raise SkillValidationError("capabilities must be a list of strings")
