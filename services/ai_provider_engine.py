"""AI provider bridge with mock-only execution for R010."""

from __future__ import annotations

from models.ai_provider import AIProviderConfig
from schemas.ai_provider_schema import validate_provider_payload


class AIProviderUnavailableError(RuntimeError):
    pass


class AIProviderRouter:
    def __init__(self, providers: list[dict]) -> None:
        self.providers = []
        for payload in providers:
            validate_provider_payload(payload)
            self.providers.append(AIProviderConfig(**payload))

    def select(self, capability: str) -> AIProviderConfig:
        for provider in self.providers:
            if provider.enabled and capability in provider.capabilities:
                return provider
        raise AIProviderUnavailableError(f"No provider supports capability: {capability}")

    def run_mock(self, capability: str, prompt: str) -> dict:
        provider = self.select(capability)
        if provider.provider_type != "mock":
            raise AIProviderUnavailableError("R010 only permits mock provider execution")
        return {
            "provider_id": provider.provider_id,
            "capability": capability,
            "output": f"[mock:{capability}] {prompt[:120]}",
            "charged": False,
        }
