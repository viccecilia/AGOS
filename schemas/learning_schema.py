"""Learning event schema validation."""

from __future__ import annotations

import re
from typing import Any

from schemas.workspace_schema import WORKSPACE_ID_PATTERN


EVENT_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{2,99}$")
TARGET_TYPES = {"content_draft", "reply_draft", "pain_point"}
SIGNALS = {"saved", "ignored", "converted", "positive_reply", "negative_reply"}


class LearningValidationError(ValueError):
    """Raised when learning event data violates the contract."""


def validate_learning_payload(payload: dict[str, Any]) -> None:
    if not WORKSPACE_ID_PATTERN.fullmatch(str(payload.get("workspace_id", ""))):
        raise LearningValidationError("learning event must bind to a valid workspace_id")
    if not EVENT_ID_PATTERN.fullmatch(str(payload.get("event_id", ""))):
        raise LearningValidationError("event_id must be 3-100 chars, lowercase letters, numbers, underscore, or hyphen")
    if str(payload.get("target_type", "")) not in TARGET_TYPES:
        raise LearningValidationError("invalid target_type")
    if not str(payload.get("target_id", "")).strip():
        raise LearningValidationError("target_id is required")
    if str(payload.get("signal", "")) not in SIGNALS:
        raise LearningValidationError("invalid learning signal")
    try:
        weight = float(payload.get("weight"))
    except (TypeError, ValueError) as exc:
        raise LearningValidationError("weight must be a number") from exc
    if weight < -100 or weight > 100:
        raise LearningValidationError("weight must be between -100 and 100")
    if not isinstance(payload.get("metadata", {}), dict):
        raise LearningValidationError("metadata must be an object")
