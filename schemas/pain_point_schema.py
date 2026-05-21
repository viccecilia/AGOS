"""Pain point radar schema validation."""

from __future__ import annotations

import re
from typing import Any

from schemas.account_matrix_schema import SUPPORTED_PLATFORMS
from schemas.workspace_schema import WORKSPACE_ID_PATTERN


PAIN_POINT_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{2,79}$")


class PainPointValidationError(ValueError):
    """Raised when pain point data violates the contract."""


def _score(name: str, value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise PainPointValidationError(f"{name} must be a number") from exc
    if number < 0 or number > 100:
        raise PainPointValidationError(f"{name} must be between 0 and 100")
    return number


def validate_pain_point_payload(payload: dict[str, Any]) -> None:
    workspace_id = str(payload.get("workspace_id", ""))
    if not WORKSPACE_ID_PATTERN.fullmatch(workspace_id):
        raise PainPointValidationError("pain point must bind to a valid workspace_id")

    pain_point_id = str(payload.get("pain_point_id", ""))
    if not PAIN_POINT_ID_PATTERN.fullmatch(pain_point_id):
        raise PainPointValidationError("pain_point_id must be 3-80 chars, lowercase letters, numbers, underscore, or hyphen")

    platform = str(payload.get("platform", ""))
    if platform not in SUPPORTED_PLATFORMS:
        raise PainPointValidationError(f"Unsupported platform: {platform}")

    for field in ["source", "market", "audience", "category", "title", "evidence"]:
        if not str(payload.get(field, "")).strip():
            raise PainPointValidationError(f"{field} is required")

    for field in ["trend_score", "urgency_score", "value_score"]:
        _score(field, payload.get(field))

    tags = payload.get("tags", [])
    if not isinstance(tags, list) or not all(isinstance(item, str) and item.strip() for item in tags):
        raise PainPointValidationError("tags must be a list of strings")

    metadata = payload.get("metadata", {})
    if not isinstance(metadata, dict):
        raise PainPointValidationError("metadata must be an object")
