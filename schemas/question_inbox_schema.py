"""Question inbox schema validation."""

from __future__ import annotations

import re
from typing import Any

from schemas.account_matrix_schema import SUPPORTED_PLATFORMS
from schemas.workspace_schema import WORKSPACE_ID_PATTERN


QUESTION_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{2,99}$")
QUESTION_STATUSES = {"new", "reviewing", "reply_ready", "replied", "ignored", "learned"}


class QuestionInboxValidationError(ValueError):
    """Raised when question candidate data violates the contract."""


def validate_question_payload(payload: dict[str, Any]) -> None:
    if not WORKSPACE_ID_PATTERN.fullmatch(str(payload.get("workspace_id", ""))):
        raise QuestionInboxValidationError("question must bind to a valid workspace_id")
    if not QUESTION_ID_PATTERN.fullmatch(str(payload.get("question_id", ""))):
        raise QuestionInboxValidationError("question_id must be 3-100 chars, lowercase letters, numbers, underscore, or hyphen")
    if str(payload.get("platform", "")) not in SUPPORTED_PLATFORMS:
        raise QuestionInboxValidationError("unsupported question platform")
    for field in ["language", "market", "audience", "question_text"]:
        if not str(payload.get(field, "")).strip():
            raise QuestionInboxValidationError(f"{field} is required")
    status = str(payload.get("status", "new"))
    if status not in QUESTION_STATUSES:
        raise QuestionInboxValidationError(f"invalid question status: {status}")
    try:
        priority_score = float(payload.get("priority_score", 0))
    except (TypeError, ValueError) as exc:
        raise QuestionInboxValidationError("priority_score must be a number") from exc
    if priority_score < 0 or priority_score > 100:
        raise QuestionInboxValidationError("priority_score must be between 0 and 100")
    for field in ["pain_points", "emotion_tags"]:
        value = payload.get(field, [])
        if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
            raise QuestionInboxValidationError(f"{field} must be a list of strings")
    if not isinstance(payload.get("metadata", {}), dict):
        raise QuestionInboxValidationError("metadata must be an object")
