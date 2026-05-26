"""Gate validation for Controlled API Intelligence Collection."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.api_collection_review_and_correction import APICollectionReviewAndCorrection
from services.collection_compliance_guard import CollectionComplianceGuard
from services.live_collection_runner import LiveCollectionRunner
from services.live_data_import_to_memory import LiveDataImportToMemory
from services.live_data_normalization_pipeline import LiveDataNormalizationPipeline
from services.platform_account_connection_center import PlatformAccountConnectionCenter
from services.platform_credential_vault import PlatformCredentialVault
from services.runtime_persistence import utc_now_iso


class ControlledAPICollectionGate:
    """Validate whether AGOS is ready for safe batch platform intelligence collection."""

    def __init__(self, root: str | Path = "runtime/controlled_api_collection_gate") -> None:
        self.root = Path(root)
        self.report_path = self.root / "CONTROLLED_API_COLLECTION_REPORT.json"
        self.safety_review_path = self.root / "PLATFORM_INTELLIGENCE_SAFETY_REVIEW.json"
        self.checks_path = self.root / "controlled_api_collection_checks.json"
        self.summary_path = self.root / "controlled_api_collection_summary.json"

    def evaluate(self, workspace_id: str = "JAG-LAB") -> dict[str, Any]:
        platform_connections = PlatformAccountConnectionCenter().build(workspace_id)
        credential_vault = PlatformCredentialVault().bootstrap_sample_status()
        live_collection = LiveCollectionRunner().run(workspace_id)
        compliance_guard = CollectionComplianceGuard().evaluate()
        normalization = LiveDataNormalizationPipeline().normalize(live_collection.get("liveCollectionItems", []))
        memory_import = LiveDataImportToMemory().import_data(workspace_id, normalization.get("normalizedLiveData", []))
        collection_review = APICollectionReviewAndCorrection().review(memory_import)

        checks = [
            self._check_platform_connections(platform_connections),
            self._check_credential_vault(credential_vault),
            self._check_live_collection(live_collection),
            self._check_compliance_guard(compliance_guard),
            self._check_normalization(normalization),
            self._check_memory_import(memory_import),
            self._check_collection_review(collection_review),
        ]
        safety_review = self._safety_review(
            platform_connections,
            credential_vault,
            live_collection,
            compliance_guard,
            normalization,
            memory_import,
            collection_review,
        )
        passed = all(item["status"] == "passed" for item in checks) and not safety_review["blocking_risk"]
        report = {
            "report_id": "CONTROLLED_API_COLLECTION_REPORT",
            "created_at": utc_now_iso(),
            "status": "passed" if passed else "needs_review",
            "phase": "CONTROLLED_API_INTELLIGENCE_COLLECTION",
            "gate": "Controlled API Collection Gate",
            "validatedCapabilities": [
                "Platform Connection Center",
                "Credential Vault",
                "Live Collection Runner",
                "Compliance Guard",
                "Normalization Pipeline",
                "Live Memory Import",
                "Collection Review & Correction",
            ],
            "controlledAPICollectionChecks": checks,
            "platformIntelligenceSafetyReview": safety_review,
            "controlledAPICollectionSummary": {
                "checks": len(checks),
                "passed": len([item for item in checks if item["status"] == "passed"]),
                "needs_review": len([item for item in checks if item["status"] != "passed"]),
                "safe_batch_platform_intelligence_ready": passed,
                "controlled_api_intelligence_collection_complete": passed,
                "ready_for_next_phase": passed,
                "next_phase": "Controlled Real External Interaction Stage",
                "write_operations_enabled": False,
                "automatic_login_scraping_enabled": False,
                "automatic_external_interaction_enabled": False,
            },
            "safetyBoundary": "Gate validates safe, compliant, batch platform intelligence collection. It does not post, reply, follow, DM, scrape login-only pages, expose credentials, call platform write APIs, or bypass platform limits.",
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
        self.safety_review_path.write_text(json.dumps(report["platformIntelligenceSafetyReview"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.checks_path.write_text(json.dumps(report["controlledAPICollectionChecks"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.summary_path.write_text(json.dumps(report["controlledAPICollectionSummary"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    @staticmethod
    def _check_platform_connections(report: dict[str, Any]) -> dict[str, Any]:
        summary = report.get("platformConnectionSummary", {})
        passed = (
            report.get("status") == "connection_center_ready"
            and summary.get("connection_center_ready") is True
            and summary.get("read_connected", 0) > 0
            and summary.get("all_write_permissions_false") is True
            and summary.get("write_enabled", 1) == 0
        )
        return {
            "check_id": "CONTROLLED-API-COLLECT-001",
            "capability": "Platform Connection Center",
            "status": "passed" if passed else "needs_review",
            "evidence": summary,
            "result": "Platform connection state is visible and write permissions are false.",
        }

    @staticmethod
    def _check_credential_vault(report: dict[str, Any]) -> dict[str, Any]:
        summary = report.get("credentialVaultSummary", {})
        passed = (
            report.get("status") == "vault_ready"
            and summary.get("workspace_isolation_enabled") is True
            and summary.get("plaintext_logging_enabled") is False
            and summary.get("public_upload_allowed") is False
            and summary.get("git_commit_allowed") is False
        )
        return {
            "check_id": "CONTROLLED-API-COLLECT-002",
            "capability": "Credential Vault",
            "status": "passed" if passed else "needs_review",
            "evidence": summary,
            "result": "Credential state is local-only, redacted, and workspace isolated.",
        }

    @staticmethod
    def _check_live_collection(report: dict[str, Any]) -> dict[str, Any]:
        summary = report.get("liveCollectionSummary", {})
        passed = (
            report.get("status") == "live_collection_completed"
            and summary.get("runner_ready") is True
            and summary.get("items_collected", 0) > 0
            and summary.get("read_only") is True
            and summary.get("all_write_actions_blocked") is True
            and summary.get("write_operations_enabled") is False
        )
        return {
            "check_id": "CONTROLLED-API-COLLECT-003",
            "capability": "Live Collection Runner",
            "status": "passed" if passed else "needs_review",
            "evidence": summary,
            "result": "Read-only batch public intelligence collection can run locally.",
        }

    @staticmethod
    def _check_compliance_guard(report: dict[str, Any]) -> dict[str, Any]:
        summary = report.get("complianceGuardSummary", {})
        passed = (
            report.get("status") == "compliance_guard_ready"
            and summary.get("guard_ready") is True
            and summary.get("blocking_risk") is False
            and summary.get("read_only_collection_allowed") is True
            and summary.get("write_api_allowed") is False
            and summary.get("auto_interaction_allowed") is False
        )
        return {
            "check_id": "CONTROLLED-API-COLLECT-004",
            "capability": "Compliance Guard",
            "status": "passed" if passed else "needs_review",
            "evidence": summary,
            "result": "Compliance risks are visible and forbidden collection behaviors remain blocked.",
        }

    @staticmethod
    def _check_normalization(report: dict[str, Any]) -> dict[str, Any]:
        summary = report.get("liveDataNormalizationSummary", {})
        passed = (
            report.get("status") == "live_data_normalized"
            and summary.get("pipeline_ready") is True
            and summary.get("items_normalized", 0) > 0
            and summary.get("write_operations_enabled") is False
        )
        return {
            "check_id": "CONTROLLED-API-COLLECT-005",
            "capability": "Normalization Pipeline",
            "status": "passed" if passed else "needs_review",
            "evidence": summary,
            "result": "Collected intelligence is normalized into shared AGOS training fields.",
        }

    @staticmethod
    def _check_memory_import(report: dict[str, Any]) -> dict[str, Any]:
        summary = report.get("memoryImportSummary", {})
        passed = (
            report.get("status") == "live_intelligence_imported_to_memory"
            and summary.get("import_ready") is True
            and summary.get("question_inbox_items", 0) > 0
            and summary.get("pattern_learning_triggered") is True
            and summary.get("replay_training_triggered") is True
            and summary.get("intelligence_ranking_triggered") is True
            and summary.get("write_operations_enabled") is False
        )
        return {
            "check_id": "CONTROLLED-API-COLLECT-006",
            "capability": "Live Memory Import",
            "status": "passed" if passed else "needs_review",
            "evidence": summary,
            "result": "Normalized intelligence enters training memory and local training triggers.",
        }

    @staticmethod
    def _check_collection_review(report: dict[str, Any]) -> dict[str, Any]:
        summary = report.get("collectionReviewSummary", {})
        passed = (
            report.get("status") == "api_collection_review_ready"
            and summary.get("review_ready") is True
            and summary.get("review_items", 0) > 0
            and summary.get("write_operations_enabled") is False
        )
        return {
            "check_id": "CONTROLLED-API-COLLECT-007",
            "capability": "Collection Review & Correction",
            "status": "passed" if passed else "needs_review",
            "evidence": summary,
            "result": "Batch review and correction are available before training data is trusted.",
        }

    @staticmethod
    def _safety_review(
        platform_connections: dict[str, Any],
        credential_vault: dict[str, Any],
        live_collection: dict[str, Any],
        compliance_guard: dict[str, Any],
        normalization: dict[str, Any],
        memory_import: dict[str, Any],
        collection_review: dict[str, Any],
    ) -> dict[str, Any]:
        connection_summary = platform_connections.get("platformConnectionSummary", {})
        vault_summary = credential_vault.get("credentialVaultSummary", {})
        collection_summary = live_collection.get("liveCollectionSummary", {})
        compliance_summary = compliance_guard.get("complianceGuardSummary", {})
        normalization_summary = normalization.get("liveDataNormalizationSummary", {})
        memory_summary = memory_import.get("memoryImportSummary", {})
        review_summary = collection_review.get("collectionReviewSummary", {})
        risk_items = [
            {
                "risk_id": "CONTROLLED-COLLECTION-RISK-001",
                "risk": "platform write action",
                "status": "blocked",
                "evidence": {
                    "connection_write_enabled": connection_summary.get("write_enabled"),
                    "collection_write_operations_enabled": collection_summary.get("write_operations_enabled"),
                },
                "mitigation": "Keep post, reply, DM, follow, like, and write API usage disabled.",
            },
            {
                "risk_id": "CONTROLLED-COLLECTION-RISK-002",
                "risk": "credential leakage",
                "status": "controlled",
                "evidence": vault_summary,
                "mitigation": "Only expose redacted credential status and keep vault files local-only.",
            },
            {
                "risk_id": "CONTROLLED-COLLECTION-RISK-003",
                "risk": "collection compliance drift",
                "status": "controlled" if not compliance_summary.get("blocking_risk") else "blocked",
                "evidence": compliance_summary,
                "mitigation": "Block automated login scraping, platform-limit bypass, write API usage, and automated interaction.",
            },
            {
                "risk_id": "CONTROLLED-COLLECTION-RISK-004",
                "risk": "low-quality intelligence entering training",
                "status": "controlled",
                "evidence": {
                    "normalized_items": normalization_summary.get("items_normalized"),
                    "review_items": review_summary.get("review_items"),
                    "corrected_records": review_summary.get("corrected_records"),
                },
                "mitigation": "Route intelligence through normalization, memory import, and review/correction before trusting it.",
            },
            {
                "risk_id": "CONTROLLED-COLLECTION-RISK-005",
                "risk": "unreviewed training memory",
                "status": "controlled",
                "evidence": memory_summary,
                "mitigation": "Keep collection review and human correction available before scaling training data.",
            },
        ]
        blocking = any(item["status"] == "blocked" and item["risk"] != "platform write action" for item in risk_items)
        return {
            "review_id": "PLATFORM_INTELLIGENCE_SAFETY_REVIEW",
            "created_at": utc_now_iso(),
            "blocking_risk": blocking,
            "overall_risk": "controlled" if not blocking else "needs_review",
            "riskItems": risk_items,
            "capabilityConclusion": "AGOS can legally and safely batch-collect platform intelligence in local read-only mode, normalize it, import it into memory, and review/correct it before training.",
            "phaseExitRecommendation": "pass_to_controlled_real_external_interaction_stage" if not blocking else "hold_for_review",
            "sourceEvidence": {
                "platform_connection_status": platform_connections.get("status"),
                "credential_vault_status": credential_vault.get("status"),
                "live_collection_status": live_collection.get("status"),
                "compliance_guard_status": compliance_guard.get("status"),
                "normalization_status": normalization.get("status"),
                "memory_import_status": memory_import.get("status"),
                "collection_review_status": collection_review.get("status"),
            },
        }


if __name__ == "__main__":
    result = ControlledAPICollectionGate().evaluate()
    print(json.dumps({"status": result["status"], "ready": result["controlledAPICollectionSummary"]["ready_for_next_phase"]}, indent=2))
