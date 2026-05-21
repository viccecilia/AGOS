"""Content draft schema validation."""

from __future__ import annotations

import re
from typing import Any

from schemas.account_matrix_schema import SUPPORTED_PLATFORMS
from schemas.workspace_schema import WORKSPACE_ID_PATTERN


CONTENT_FORMATS = {"post", "short_video", "reply_seed", "youtube_outline", "seo_article"}
REVIEW_STATUSES = {"needs_review", "approved", "rejected"}
DRAFT_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{2,99}$")


class ContentValidationError(ValueError):
    """Raised when content draft data violates the contract."""


def validate_content_payload(payload: dict[str, Any]) -> None:
    workspace_id = str(payload.get("workspace_id", ""))
    if not WORKSPACE_ID_PATTERN.fullmatch(workspace_id):
        raise ContentValidationError("content draft must bind to a valid workspace_id")

    draft_id = str(payload.get("draft_id", ""))
    if not DRAFT_ID_PATTERN.fullmatch(draft_id):
        raise ContentValidationError("draft_id must be 3-100 chars, lowercase letters, numbers, underscore, or hyphen")

    platform = str(payload.get("platform", ""))
    if platform not in SUPPORTED_PLATFORMS:
        raise ContentValidationError(f"Unsupported platform: {platform}")

    content_format = str(payload.get("format", ""))
    if content_format not in CONTENT_FORMATS:
        raise ContentValidationError(f"Unsupported content format: {content_format}")

    review_status = str(payload.get("review_status", "needs_review"))
    if review_status not in REVIEW_STATUSES:
        raise ContentValidationError(f"Invalid review status: {review_status}")

    for field in ["pain_point_id", "title", "hook", "body"]:
        if not str(payload.get(field, "")).strip():
            raise ContentValidationError(f"{field} is required")

    tags = payload.get("tags", [])
    if not isinstance(tags, list) or not all(isinstance(item, str) and item.strip() for item in tags):
        raise ContentValidationError("tags must be a list of strings")

    metadata = payload.get("metadata", {})
    if not isinstance(metadata, dict):
        raise ContentValidationError("metadata must be an object")
