"""Report schema validation."""

from __future__ import annotations

import re
from typing import Any

from schemas.workspace_schema import WORKSPACE_ID_PATTERN


REPORT_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{2,99}$")
REPORT_TYPES = {"daily", "weekly", "monthly"}


class ReportValidationError(ValueError):
    """Raised when report data violates the contract."""


def validate_report_payload(payload: dict[str, Any]) -> None:
    if not WORKSPACE_ID_PATTERN.fullmatch(str(payload.get("workspace_id", ""))):
        raise ReportValidationError("report must bind to a valid workspace_id")
    if not REPORT_ID_PATTERN.fullmatch(str(payload.get("report_id", ""))):
        raise ReportValidationError("report_id must be 3-100 chars, lowercase letters, numbers, underscore, or hyphen")
    if str(payload.get("report_type", "")) not in REPORT_TYPES:
        raise ReportValidationError("invalid report_type")
    for field in ["title", "summary"]:
        if not str(payload.get(field, "")).strip():
            raise ReportValidationError(f"{field} is required")
    if not isinstance(payload.get("metrics", {}), dict):
        raise ReportValidationError("metrics must be an object")
    recommendations = payload.get("recommendations", [])
    if not isinstance(recommendations, list) or not all(isinstance(item, str) for item in recommendations):
        raise ReportValidationError("recommendations must be a list of strings")
