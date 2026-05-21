"""Account matrix schema validation."""

from __future__ import annotations

import re
from typing import Any

from schemas.workspace_schema import WORKSPACE_ID_PATTERN


SUPPORTED_PLATFORMS = {"tiktok", "instagram", "x", "youtube", "reddit", "threads", "seo"}
ACCOUNT_STATUSES = {"draft", "active", "paused", "needs_review", "archived"}
RISK_STATUSES = {"normal", "watch", "restricted", "blocked"}
ACCOUNT_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{2,79}$")
SENSITIVE_KEYS = {"password", "token", "cookie", "secret", "api_key", "access_token", "refresh_token"}


class AccountMatrixValidationError(ValueError):
    """Raised when an account profile violates the account matrix contract."""


def validate_account_payload(payload: dict[str, Any]) -> None:
    workspace_id = str(payload.get("workspace_id", ""))
    if not WORKSPACE_ID_PATTERN.fullmatch(workspace_id):
        raise AccountMatrixValidationError("account profile must bind to a valid workspace_id")

    account_id = str(payload.get("account_id", ""))
    if not ACCOUNT_ID_PATTERN.fullmatch(account_id):
        raise AccountMatrixValidationError("account_id must be 3-80 chars, lowercase letters, numbers, underscore, or hyphen")

    platform = str(payload.get("platform", ""))
    if platform not in SUPPORTED_PLATFORMS:
        raise AccountMatrixValidationError(f"Unsupported platform: {platform}")

    status = str(payload.get("status", "draft"))
    if status not in ACCOUNT_STATUSES:
        raise AccountMatrixValidationError(f"Invalid account status: {status}")

    risk_status = str(payload.get("risk_status", "normal"))
    if risk_status not in RISK_STATUSES:
        raise AccountMatrixValidationError(f"Invalid risk status: {risk_status}")

    for field in ["handle", "display_name"]:
        if not str(payload.get(field, "")).strip():
            raise AccountMatrixValidationError(f"{field} is required")

    metadata = payload.get("metadata", {})
    if not isinstance(metadata, dict):
        raise AccountMatrixValidationError("metadata must be an object")
    leaked_keys = sorted(SENSITIVE_KEYS.intersection({str(key).lower() for key in metadata.keys()}))
    if leaked_keys:
        raise AccountMatrixValidationError(f"Sensitive metadata is not allowed: {', '.join(leaked_keys)}")
