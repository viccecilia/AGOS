from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from schemas.ai_provider_schema import AIProviderValidationError
from services.ai_provider_engine import AIProviderRouter, AIProviderUnavailableError


def main() -> None:
    router = AIProviderRouter(
        [
            {
                "provider_id": "mock_primary",
                "provider_type": "mock",
                "display_name": "Mock Primary",
                "capabilities": ["text", "content_draft", "reply_draft"],
                "monthly_quota": 1000,
                "enabled": True,
            }
        ]
    )
    result = router.run_mock("content_draft", "Create a travel post draft")
    assert result["provider_id"] == "mock_primary"
    assert result["charged"] is False

    try:
        AIProviderRouter(
            [
                {
                    "provider_id": "bad_secret",
                    "provider_type": "mock",
                    "display_name": "Bad",
                    "capabilities": ["text"],
                    "api_key": "must-not-store",
                }
            ]
        )
        raise AssertionError("Secret field was accepted")
    except AIProviderValidationError:
        pass

    try:
        router.run_mock("report_summary", "No provider")
        raise AssertionError("Missing capability was accepted")
    except AIProviderUnavailableError:
        pass

    print("ai provider smoke test passed")


if __name__ == "__main__":
    main()
