"""Gate validation for the Platform API Scout Integration phase."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.api_capability_registry import APICapabilityRegistry
from services.api_rate_limit_guard import APIRateLimitGuard
from services.api_signal_normalization import APISignalNormalization
from services.api_to_scout_pipeline import APIToScoutPipeline
from services.platform_credential_vault import PlatformCredentialVault
from services.read_only_trend_connector import ReadOnlyTrendConnector
from services.runtime_persistence import utc_now_iso


class APIScoutGate:
    """Validate whether AGOS can safely read platform trend intelligence."""

    def __init__(self, root: str | Path = "runtime/api_scout_gate") -> None:
        self.root = Path(root)
        self.report_path = self.root / "API_SCOUT_VALIDATION_REPORT.json"
        self.risk_review_path = self.root / "PLATFORM_API_RISK_REVIEW.json"
        self.checks_path = self.root / "api_scout_gate_checks.json"

    def evaluate(self) -> dict[str, Any]:
        registry = APICapabilityRegistry().state()
        vault = PlatformCredentialVault().bootstrap_sample_status()
        trends = ReadOnlyTrendConnector().state()
        safety = APIRateLimitGuard().state()
        normalization = APISignalNormalization().state()
        pipeline = APIToScoutPipeline().state()

        checks = [
            self._check_registry(registry),
            self._check_vault(vault),
            self._check_trend_connector(trends),
            self._check_safety_guard(safety),
            self._check_signal_normalization(normalization),
            self._check_api_scout_pipeline(pipeline),
        ]
        risk_review = self._risk_review(registry, vault, trends, safety, normalization, pipeline)
        passed = all(item["status"] == "passed" for item in checks) and not risk_review["blocking_risk"]
        report = {
            "report_id": "API_SCOUT_VALIDATION_REPORT",
            "created_at": utc_now_iso(),
            "status": "passed" if passed else "needs_review",
            "phase": "PLATFORM_API_SCOUT_INTEGRATION",
            "gate": "API Scout Gate",
            "validatedCapabilities": [
                "API Registry",
                "Credential Vault",
                "Trend Connector",
                "API Safety Guard",
                "Signal Normalization",
                "API Scout Pipeline",
            ],
            "apiScoutGateChecks": checks,
            "platformApiRiskReview": risk_review,
            "apiScoutGateSummary": {
                "checks": len(checks),
                "passed": len([item for item in checks if item["status"] == "passed"]),
                "needs_review": len([item for item in checks if item["status"] != "passed"]),
                "safe_trend_intelligence_ready": passed,
                "ready_for_next_phase": passed,
                "next_phase": "Controlled External Operations Preparation Stage",
                "write_operations_enabled": False,
            },
            "safetyBoundary": "Gate validates safe read-only platform trend intelligence. It does not post, reply, follow, DM, scrape login-only pages, expose credentials, or bypass platform limits.",
        }
        self.persist(report)
        return report

    def state(self) -> dict[str, Any]:
        if self.report_path.exists():
            return json.loads(self.report_path.read_text(encoding="utf-8"))
        return self.evaluate()

    def persist(self, report: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.risk_review_path.write_text(json.dumps(report["platformApiRiskReview"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.checks_path.write_text(json.dumps(report["apiScoutGateChecks"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    @staticmethod
    def _check_registry(registry: dict[str, Any]) -> dict[str, Any]:
        summary = registry.get("apiRegistrySummary", {})
        passed = (
            registry.get("status") == "registry_ready"
            and summary.get("external_api_calls_enabled") is False
            and summary.get("all_platforms_block_auto_posting") is True
            and summary.get("all_platforms_block_auto_reply") is True
        )
        return {
            "check_id": "API-GATE-001",
            "capability": "API Registry",
            "status": "passed" if passed else "needs_review",
            "evidence": summary,
            "result": "Platform API capabilities and forbidden actions are explicitly registered.",
        }

    @staticmethod
    def _check_vault(vault: dict[str, Any]) -> dict[str, Any]:
        summary = vault.get("credentialVaultSummary", {})
        passed = (
            vault.get("status") == "vault_ready"
            and summary.get("workspace_isolation_enabled") is True
            and summary.get("plaintext_logging_enabled") is False
            and summary.get("public_upload_allowed") is False
            and summary.get("git_commit_allowed") is False
        )
        return {
            "check_id": "API-GATE-002",
            "capability": "Credential Vault",
            "status": "passed" if passed else "needs_review",
            "evidence": summary,
            "result": "Credentials are local-only, redacted, and workspace isolated.",
        }

    @staticmethod
    def _check_trend_connector(trends: dict[str, Any]) -> dict[str, Any]:
        summary = trends.get("trendConnectorSummary", {})
        passed = (
            trends.get("status") == "trends_read"
            and summary.get("trends_read", 0) > 0
            and summary.get("read_only") is True
            and summary.get("write_operations_enabled") is False
        )
        return {
            "check_id": "API-GATE-003",
            "capability": "Trend Connector",
            "status": "passed" if passed else "needs_review",
            "evidence": summary,
            "result": "Read-only platform trend signals are available locally.",
        }

    @staticmethod
    def _check_safety_guard(safety: dict[str, Any]) -> dict[str, Any]:
        summary = safety.get("apiRiskSummary", {})
        passed = (
            safety.get("status") == "safety_guard_ready"
            and summary.get("write_operations_enabled") is False
            and summary.get("blocked", 0) == 0
        )
        return {
            "check_id": "API-GATE-004",
            "capability": "API Safety Guard",
            "status": "passed" if passed else "needs_review",
            "evidence": summary,
            "result": "Rate-limit and suspicious-pattern risk is visible before external usage.",
        }

    @staticmethod
    def _check_signal_normalization(normalization: dict[str, Any]) -> dict[str, Any]:
        summary = normalization.get("normalizationSummary", {})
        passed = (
            normalization.get("status") == "signals_normalized"
            and summary.get("signals_normalized", 0) > 0
            and summary.get("platforms", 0) >= 4
            and summary.get("write_operations_enabled") is False
        )
        return {
            "check_id": "API-GATE-005",
            "capability": "Signal Normalization",
            "status": "passed" if passed else "needs_review",
            "evidence": summary,
            "result": "Different platform signals are unified into shared Scout fields.",
        }

    @staticmethod
    def _check_api_scout_pipeline(pipeline: dict[str, Any]) -> dict[str, Any]:
        summary = pipeline.get("apiScoutPipelineSummary", {})
        passed = (
            pipeline.get("status") == "api_trends_entered_scout_intelligence"
            and summary.get("api_trends_entered_scout") is True
            and summary.get("strategic_interpretations", 0) > 0
            and summary.get("write_operations_enabled") is False
        )
        return {
            "check_id": "API-GATE-006",
            "capability": "API Scout Pipeline",
            "status": "passed" if passed else "needs_review",
            "evidence": summary,
            "result": "Read-only API trends enter Scout Intelligence and reach strategic interpretation.",
        }

    @staticmethod
    def _risk_review(
        registry: dict[str, Any],
        vault: dict[str, Any],
        trends: dict[str, Any],
        safety: dict[str, Any],
        normalization: dict[str, Any],
        pipeline: dict[str, Any],
    ) -> dict[str, Any]:
        risk_items = [
            {
                "risk_id": "API-RISK-001",
                "risk": "write-side automation",
                "status": "blocked",
                "evidence": "auto posting, auto reply, auto follow, auto DM, and auto engagement are forbidden in API Registry.",
                "mitigation": "Keep all external platform actions human-gated and disabled.",
            },
            {
                "risk_id": "API-RISK-002",
                "risk": "credential leakage",
                "status": "controlled",
                "evidence": vault.get("credentialVaultSummary", {}),
                "mitigation": "Keep vault files local-only and excluded from Git; expose only redacted status.",
            },
            {
                "risk_id": "API-RISK-003",
                "risk": "platform rate-limit pressure",
                "status": "watch" if safety.get("apiRiskSummary", {}).get("approaching_platform_risk") else "controlled",
                "evidence": safety.get("apiRiskSummary", {}),
                "mitigation": "Require slow-down and human review when near_platform_risk appears.",
            },
            {
                "risk_id": "API-RISK-004",
                "risk": "misinterpreting platform signals",
                "status": "controlled",
                "evidence": normalization.get("normalizationSummary", {}),
                "mitigation": "Use normalized language, emotion, strength, and engagement fields before Scout ranking.",
            },
            {
                "risk_id": "API-RISK-005",
                "risk": "unsafe Scout escalation",
                "status": "controlled",
                "evidence": pipeline.get("apiScoutPipelineSummary", {}),
                "mitigation": "Route API trends through Scout Intelligence locally before any external operation.",
            },
        ]
        return {
            "review_id": "PLATFORM_API_RISK_REVIEW",
            "created_at": utc_now_iso(),
            "blocking_risk": False,
            "overall_risk": "medium_watch" if any(item["status"] == "watch" for item in risk_items) else "controlled",
            "riskItems": risk_items,
            "capabilityConclusion": "AGOS can safely read and interpret platform trend intelligence locally, with write actions blocked and risk visible.",
            "phaseExitRecommendation": "pass_to_controlled_external_operations_preparation",
            "sourceEvidence": {
                "registry_status": registry.get("status"),
                "trend_status": trends.get("status"),
                "normalization_status": normalization.get("status"),
                "pipeline_status": pipeline.get("status"),
            },
        }


if __name__ == "__main__":
    result = APIScoutGate().evaluate()
    print(json.dumps({"status": result["status"], "ready": result["apiScoutGateSummary"]["ready_for_next_phase"]}, indent=2))
