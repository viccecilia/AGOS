"""Reply attempt schema validation."""

from __future__ import annotations

import re
from typing import Any

from schemas.account_matrix_schema import SUPPORTED_PLATFORMS
from schemas.answer_branch_schema import BRANCH_ID_PATTERN
from schemas.question_inbox_schema import QUESTION_ID_PATTERN
from schemas.workspace_schema import WORKSPACE_ID_PATTERN


REPLY_ATTEMPT_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{2,99}$")
REPLY_ATTEMPT_STATUSES = {"draft", "approved", "posted", "ignored", "high_engagement"}


class ReplyAttemptValidationError(ValueError):
    """Raised when reply attempt data violates the contract."""


def _count(name: str, value: Any) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ReplyAttemptValidationError(f"{name} must be an integer") from exc
    if number < 0:
        raise ReplyAttemptValidationError(f"{name} must be >= 0")
    return number


def validate_reply_attempt_payload(payload: dict[str, Any]) -> None:
    if not WORKSPACE_ID_PATTERN.fullmatch(str(payload.get("workspace_id", ""))):
        raise ReplyAttemptValidationError("reply attempt must bind to a valid workspace_id")
    if not REPLY_ATTEMPT_ID_PATTERN.fullmatch(str(payload.get("reply_attempt_id", ""))):
        raise ReplyAttemptValidationError("reply_attempt_id must be 3-100 chars, lowercase letters, numbers, underscore, or hyphen")
    if not QUESTION_ID_PATTERN.fullmatch(str(payload.get("question_id", ""))):
        raise ReplyAttemptValidationError("reply attempt must bind to a valid question_id")
    if not BRANCH_ID_PATTERN.fullmatch(str(payload.get("branch_id", ""))):
        raise ReplyAttemptValidationError("reply attempt must bind to a valid branch_id")
    if str(payload.get("platform", "")) not in SUPPORTED_PLATFORMS:
        raise ReplyAttemptValidationError("unsupported reply attempt platform")
    if str(payload.get("status", "draft")) not in REPLY_ATTEMPT_STATUSES:
        raise ReplyAttemptValidationError("invalid reply attempt status")
    for field in ["liked", "replied", "ignored", "saved", "shared"]:
        _count(field, payload.get(field, 0))
    if not isinstance(payload.get("metadata", {}), dict):
        raise ReplyAttemptValidationError("metadata must be an object")
