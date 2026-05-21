"""Workspace schema validation."""

from __future__ import annotations

import re
from typing import Any


WORKSPACE_STATUSES = {"draft", "active", "paused", "archived"}
WORKSPACE_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{2,63}$")


class WorkspaceValidationError(ValueError):
    """Raised when workspace data violates the workspace contract."""


def validate_workspace_payload(payload: dict[str, Any]) -> None:
    required = ["workspace_id", "name", "owner", "product_name", "industry"]
    missing = [field for field in required if not str(payload.get(field, "")).strip()]
    if missing:
        raise WorkspaceValidationError(f"Missing required workspace fields: {', '.join(missing)}")

    workspace_id = str(payload["workspace_id"])
    if not WORKSPACE_ID_PATTERN.fullmatch(workspace_id):
        raise WorkspaceValidationError(
            "workspace_id must be 3-64 chars, lowercase letters, numbers, underscore, or hyphen"
        )

    status = str(payload.get("status", "draft"))
    if status not in WORKSPACE_STATUSES:
        raise WorkspaceValidationError(f"Invalid workspace status: {status}")

    target_markets = payload.get("target_markets", [])
    if not isinstance(target_markets, list) or not all(isinstance(item, str) for item in target_markets):
        raise WorkspaceValidationError("target_markets must be a list of strings")

    metadata = payload.get("metadata", {})
    if not isinstance(metadata, dict):
        raise WorkspaceValidationError("metadata must be an object")
