"""Credential vault contract and secret boundary for real-data access."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.runtime_persistence import utc_now_iso


DEFAULT_OUTPUT_DIR = Path("runtime/real_data_access")

MVP_PLATFORM_IDS = ["youtube", "tiktok", "instagram"]
OPTIONAL_PLATFORM_IDS = [
    "x_twitter",
    "reddit",
    "facebook_page",
    "linkedin",
    "xiaohongshu",
    "douyin",
    "bilibili",
]
FORBIDDEN_CREDENTIAL_HANDLING = [
    "no tokens in Git",
    "no tokens in runtime JSON",
    "no .env writes by AGOS",
    "no logs containing secrets",
    "no screenshots containing secrets",
]
ALLOWED_CREDENTIAL_HANDLING = [
    "external vault reference",
    "local operator-provided runtime injection",
    "least-privilege scopes",
    "revocation support",
    "rotation support",
]


class CredentialVaultContract:
    """Create secret boundary artifacts without requesting or storing secrets."""

    def __init__(self, output_dir: str | Path = DEFAULT_OUTPUT_DIR) -> None:
        self.output_dir = Path(output_dir)
        self.contract_path = self.output_dir / "CREDENTIAL_VAULT_CONTRACT.json"
        self.policy_path = self.output_dir / "SECRET_BOUNDARY_POLICY.json"
        self.audit_template_path = self.output_dir / "CREDENTIAL_AUDIT_TEMPLATE.json"
        self.evidence_path = self.output_dir / "SECRET_BOUNDARY_EVIDENCE.json"

    def build(self) -> dict[str, Any]:
        created_at = utc_now_iso()
        audit_template = self._audit_template(created_at)
        policy = self._secret_boundary_policy(created_at)
        contract = {
            "contract_id": "CREDENTIAL_VAULT_CONTRACT",
            "round_id": "ROUND-REALDATA-002_CREDENTIAL_VAULT_AND_SECRET_BOUNDARY",
            "phase": "AGOS_REAL_DATA_CONTROLLED_ACCESS",
            "created_at": created_at,
            "status": "credential_contract_defined_no_secrets",
            "supportedPlatformIds": MVP_PLATFORM_IDS,
            "optionalLaterPlatformIds": OPTIONAL_PLATFORM_IDS,
            "forbiddenCredentialHandling": FORBIDDEN_CREDENTIAL_HANDLING,
            "allowedCredentialHandling": ALLOWED_CREDENTIAL_HANDLING,
            "credentialReferencePolicy": {
                "store_reference_only": True,
                "secret_value_storage_allowed": False,
                "runtime_json_secret_storage_allowed": False,
                "git_secret_storage_allowed": False,
                "env_write_allowed_by_agos": False,
                "log_secret_allowed": False,
                "screenshot_secret_allowed": False,
            },
            "allowedReferenceTypes": [
                "external_vault_reference",
                "operator_runtime_injection_reference",
                "platform_developer_console_reference",
            ],
            "credentialAuditTemplate": audit_template,
            "secretBoundaryPolicy": policy,
        }
        evidence = self._evidence(contract, policy, audit_template, created_at)
        contract["secretBoundaryEvidence"] = evidence
        self.persist(contract)
        return contract

    def state(self) -> dict[str, Any]:
        if self.contract_path.exists():
            return json.loads(self.contract_path.read_text(encoding="utf-8"))
        return self.build()

    def persist(self, contract: dict[str, Any]) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.contract_path.write_text(json.dumps(contract, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.policy_path.write_text(json.dumps(contract["secretBoundaryPolicy"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.audit_template_path.write_text(json.dumps(contract["credentialAuditTemplate"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.evidence_path.write_text(json.dumps(contract["secretBoundaryEvidence"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    @staticmethod
    def _audit_template(created_at: str) -> dict[str, Any]:
        rows = []
        for platform_id in [*MVP_PLATFORM_IDS, *OPTIONAL_PLATFORM_IDS]:
            rows.append(
                {
                    "platform_id": platform_id,
                    "credential_reference_id": f"vault_ref_{platform_id}_read_only_placeholder",
                    "scope_summary": "read_only_public_metadata_or_analytics_only",
                    "owner_approval_status": "not_requested",
                    "rotation_required": True,
                    "last_verified_at": None,
                    "revocation_supported": True,
                    "least_privilege_required": True,
                    "secret_value_present": False,
                    "token_in_git": False,
                    "token_in_runtime_json": False,
                    "env_written_by_agos": False,
                    "logs_contain_secret": False,
                    "screenshots_contain_secret": False,
                }
            )
        return {
            "template_id": "CREDENTIAL_AUDIT_TEMPLATE",
            "round_id": "ROUND-REALDATA-002_CREDENTIAL_VAULT_AND_SECRET_BOUNDARY",
            "created_at": created_at,
            "credentialAuditFields": [
                "platform_id",
                "credential_reference_id",
                "scope_summary",
                "owner_approval_status",
                "rotation_required",
                "last_verified_at",
            ],
            "credentialAuditRows": rows,
            "real_credentials_included": False,
            "template_only": True,
        }

    @staticmethod
    def _secret_boundary_policy(created_at: str) -> dict[str, Any]:
        return {
            "policy_id": "SECRET_BOUNDARY_POLICY",
            "round_id": "ROUND-REALDATA-002_CREDENTIAL_VAULT_AND_SECRET_BOUNDARY",
            "created_at": created_at,
            "forbiddenCredentialHandling": FORBIDDEN_CREDENTIAL_HANDLING,
            "allowedCredentialHandling": ALLOWED_CREDENTIAL_HANDLING,
            "storagePolicy": {
                "git_tokens_allowed": False,
                "runtime_json_tokens_allowed": False,
                "agos_env_writes_allowed": False,
                "logs_containing_secrets_allowed": False,
                "screenshots_containing_secrets_allowed": False,
                "password_storage_allowed": False,
                "private_message_scope_allowed": False,
            },
            "allowedHandlingPolicy": {
                "external_vault_reference_allowed": True,
                "operator_runtime_injection_allowed": True,
                "least_privilege_scopes_required": True,
                "revocation_support_required": True,
                "rotation_support_required": True,
            },
            "executionBoundary": {
                "real_platform_api_called": False,
                "real_data_ingested": False,
                "agos_training_started": False,
                "write_api_allowed": False,
            },
        }

    @staticmethod
    def _evidence(
        contract: dict[str, Any],
        policy: dict[str, Any],
        audit_template: dict[str, Any],
        created_at: str,
    ) -> dict[str, Any]:
        storage_policy = policy["storagePolicy"]
        execution_boundary = policy["executionBoundary"]
        return {
            "evidence_id": "SECRET_BOUNDARY_EVIDENCE",
            "round_id": "ROUND-REALDATA-002_CREDENTIAL_VAULT_AND_SECRET_BOUNDARY",
            "created_at": created_at,
            "evidence_status": "secret_boundary_defined_no_real_secrets",
            "credential_vault_contract_defined": True,
            "secret_boundary_policy_defined": True,
            "credential_audit_template_defined": True,
            "real_secrets_requested_in_chat": False,
            "real_tokens_stored": False,
            "tokens_in_git_allowed": storage_policy["git_tokens_allowed"],
            "tokens_in_runtime_json_allowed": storage_policy["runtime_json_tokens_allowed"],
            "env_writes_by_agos_allowed": storage_policy["agos_env_writes_allowed"],
            "logs_containing_secrets_allowed": storage_policy["logs_containing_secrets_allowed"],
            "screenshots_containing_secrets_allowed": storage_policy["screenshots_containing_secrets_allowed"],
            "external_vault_reference_allowed": policy["allowedHandlingPolicy"]["external_vault_reference_allowed"],
            "operator_runtime_injection_allowed": policy["allowedHandlingPolicy"]["operator_runtime_injection_allowed"],
            "least_privilege_scopes_required": policy["allowedHandlingPolicy"]["least_privilege_scopes_required"],
            "revocation_support_required": policy["allowedHandlingPolicy"]["revocation_support_required"],
            "rotation_support_required": policy["allowedHandlingPolicy"]["rotation_support_required"],
            "audit_row_count": len(audit_template["credentialAuditRows"]),
            "real_platform_api_called": execution_boundary["real_platform_api_called"],
            "real_data_ingested": execution_boundary["real_data_ingested"],
            "agos_training_started": execution_boundary["agos_training_started"],
            "write_api_allowed": execution_boundary["write_api_allowed"],
            "next_gate_required": "ROUND-REALDATA-003_READ_ONLY_CONNECTION_DRY_RUN",
        }


if __name__ == "__main__":
    report = CredentialVaultContract().build()
    print(json.dumps(report["secretBoundaryEvidence"], ensure_ascii=True, indent=2, sort_keys=True))
