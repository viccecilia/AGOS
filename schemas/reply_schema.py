"""Reply draft schema validation."""

from __future__ import annotations

import re
from typing import Any

from schemas.account_matrix_schema import SUPPORTED_PLATFORMS
from schemas.workspace_schema import WORKSPACE_ID_PATTERN


REPLY_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{2,99}$")
REVIEW_STATUSES = {"needs_review", "approved", "rejected"}
RISK_LEVELS = {"normal", "watch", "blocked"}


class ReplyValidationError(ValueError):
    """Raised when reply draft data violates the contract."""


def validate_reply_payload(payload: dict[str, Any]) -> None:
    workspace_id = str(payload.get("workspace_id", ""))
    if not WORKSPACE_ID_PATTERN.fullmatch(workspace_id):
        raise ReplyValidationError("reply draft must bind to a valid workspace_id")

    reply_id = str(payload.get("reply_id", ""))
    if not REPLY_ID_PATTERN.fullmatch(reply_id):
        raise ReplyValidationError("reply_id must be 3-100 chars, lowercase letters, numbers, underscore, or hyphen")

    platform = str(payload.get("source_platform", ""))
    if platform not in SUPPORTED_PLATFORMS:
        raise ReplyValidationError(f"Unsupported source platform: {platform}")

    review_status = str(payload.get("review_status", "needs_review"))
    if review_status not in REVIEW_STATUSES:
        raise ReplyValidationError(f"Invalid review status: {review_status}")

    risk_level = str(payload.get("risk_level", "normal"))
    if risk_level not in RISK_LEVELS:
        raise ReplyValidationError(f"Invalid risk level: {risk_level}")

    for field in ["source_text", "draft_text"]:
        if not str(payload.get(field, "")).strip():
            raise ReplyValidationError(f"{field} is required")

    risk_reasons = payload.get("risk_reasons", [])
    if not isinstance(risk_reasons, list) or not all(isinstance(item, str) for item in risk_reasons):
        raise ReplyValidationError("risk_reasons must be a list of strings")
