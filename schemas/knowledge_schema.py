"""Knowledge base schema validation."""

from __future__ import annotations

from typing import Any

from schemas.workspace_schema import WORKSPACE_ID_PATTERN


class KnowledgeValidationError(ValueError):
    """Raised when knowledge base data violates the contract."""


def _validate_string_list(name: str, value: Any) -> None:
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        raise KnowledgeValidationError(f"{name} must be a non-empty string list when provided")


def _validate_dict_list(name: str, value: Any, required_keys: set[str]) -> None:
    if not isinstance(value, list):
        raise KnowledgeValidationError(f"{name} must be a list")
    for item in value:
        if not isinstance(item, dict):
            raise KnowledgeValidationError(f"{name} entries must be objects")
        missing = [key for key in required_keys if not str(item.get(key, "")).strip()]
        if missing:
            raise KnowledgeValidationError(f"{name} entry missing: {', '.join(missing)}")


def validate_knowledge_payload(payload: dict[str, Any]) -> None:
    workspace_id = str(payload.get("workspace_id", ""))
    if not WORKSPACE_ID_PATTERN.fullmatch(workspace_id):
        raise KnowledgeValidationError("knowledge base must bind to a valid workspace_id")

    if not str(payload.get("brand_voice", "")).strip():
        raise KnowledgeValidationError("brand_voice is required")

    _validate_dict_list("product_facts", payload.get("product_facts", []), {"title", "detail"})
    _validate_dict_list("faqs", payload.get("faqs", []), {"question", "answer"})
    _validate_string_list("industry_notes", payload.get("industry_notes", []))
    _validate_dict_list("content_templates", payload.get("content_templates", []), {"name", "template"})

    metadata = payload.get("metadata", {})
    if not isinstance(metadata, dict):
        raise KnowledgeValidationError("metadata must be an object")
