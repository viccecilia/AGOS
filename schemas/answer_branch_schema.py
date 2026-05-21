"""Answer branch schema validation."""

from __future__ import annotations

import re
from typing import Any

from schemas.account_matrix_schema import SUPPORTED_PLATFORMS
from schemas.question_inbox_schema import QUESTION_ID_PATTERN
from schemas.workspace_schema import WORKSPACE_ID_PATTERN


BRANCH_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{2,99}$")
BRANCH_REVIEW_STATUSES = {"needs_review", "approved", "rejected"}


class AnswerBranchValidationError(ValueError):
    """Raised when answer branch data violates the contract."""


def _score(name: str, value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise AnswerBranchValidationError(f"{name} must be a number") from exc
    if number < 0 or number > 100:
        raise AnswerBranchValidationError(f"{name} must be between 0 and 100")
    return number


def validate_answer_branch_payload(payload: dict[str, Any]) -> None:
    if not WORKSPACE_ID_PATTERN.fullmatch(str(payload.get("workspace_id", ""))):
        raise AnswerBranchValidationError("answer branch must bind to a valid workspace_id")
    if not BRANCH_ID_PATTERN.fullmatch(str(payload.get("branch_id", ""))):
        raise AnswerBranchValidationError("branch_id must be 3-100 chars, lowercase letters, numbers, underscore, or hyphen")
    if not QUESTION_ID_PATTERN.fullmatch(str(payload.get("question_id", ""))):
        raise AnswerBranchValidationError("answer branch must bind to a valid question_id")
    if str(payload.get("platform", "")) not in SUPPORTED_PLATFORMS:
        raise AnswerBranchValidationError("unsupported answer branch platform")
    for field in ["tone", "reply_text"]:
        if not str(payload.get(field, "")).strip():
            raise AnswerBranchValidationError(f"{field} is required")
    for field in ["engagement_score", "ignore_score", "save_score"]:
        _score(field, payload.get(field, 0))
    if str(payload.get("review_status", "needs_review")) not in BRANCH_REVIEW_STATUSES:
        raise AnswerBranchValidationError("invalid review_status")
    if not isinstance(payload.get("best_answer", False), bool):
        raise AnswerBranchValidationError("best_answer must be boolean")
    if not isinstance(payload.get("metadata", {}), dict):
        raise AnswerBranchValidationError("metadata must be an object")
