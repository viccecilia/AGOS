"""AI provider schema validation."""

from __future__ import annotations

import re
from typing import Any


PROVIDER_TYPES = {"mock", "openai", "deepseek", "claude", "custom", "local"}
CAPABILITIES = {"text", "classification", "content_draft", "reply_draft", "report_summary"}
PROVIDER_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{2,79}$")
FORBIDDEN_KEYS = {"api_key", "secret", "token", "password", "access_token", "refresh_token"}


class AIProviderValidationError(ValueError):
    pass


def validate_provider_payload(payload: dict[str, Any]) -> None:
    if not PROVIDER_ID_PATTERN.fullmatch(str(payload.get("provider_id", ""))):
        raise AIProviderValidationError("invalid provider_id")
    if str(payload.get("provider_type", "")) not in PROVIDER_TYPES:
        raise AIProviderValidationError("invalid provider_type")
    if not str(payload.get("display_name", "")).strip():
        raise AIProviderValidationError("display_name is required")
    capabilities = payload.get("capabilities", [])
    if not isinstance(capabilities, list) or not set(capabilities).issubset(CAPABILITIES):
        raise AIProviderValidationError("invalid capabilities")
    if int(payload.get("monthly_quota", 0)) < 0:
        raise AIProviderValidationError("monthly_quota must be non-negative")
    leaked = FORBIDDEN_KEYS.intersection({str(key).lower() for key in payload.keys()})
    if leaked:
        raise AIProviderValidationError(f"forbidden secret fields: {', '.join(sorted(leaked))}")
