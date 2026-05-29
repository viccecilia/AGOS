from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.credential_vault_contract import CredentialVaultContract


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp) / "real_data_access"
        report = CredentialVaultContract(output_dir).build()

        assert report["contract_id"] == "CREDENTIAL_VAULT_CONTRACT"
        assert report["round_id"] == "ROUND-REALDATA-002_CREDENTIAL_VAULT_AND_SECRET_BOUNDARY"
        assert report["status"] == "credential_contract_defined_no_secrets"

        forbidden = set(report["forbiddenCredentialHandling"])
        for item in [
            "no tokens in Git",
            "no tokens in runtime JSON",
            "no .env writes by AGOS",
            "no logs containing secrets",
            "no screenshots containing secrets",
        ]:
            assert item in forbidden

        allowed = set(report["allowedCredentialHandling"])
        for item in [
            "external vault reference",
            "local operator-provided runtime injection",
            "least-privilege scopes",
            "revocation support",
            "rotation support",
        ]:
            assert item in allowed

        ref_policy = report["credentialReferencePolicy"]
        assert ref_policy["store_reference_only"] is True
        assert ref_policy["secret_value_storage_allowed"] is False
        assert ref_policy["runtime_json_secret_storage_allowed"] is False
        assert ref_policy["git_secret_storage_allowed"] is False
        assert ref_policy["env_write_allowed_by_agos"] is False
        assert ref_policy["log_secret_allowed"] is False
        assert ref_policy["screenshot_secret_allowed"] is False

        audit = report["credentialAuditTemplate"]
        for field in [
            "platform_id",
            "credential_reference_id",
            "scope_summary",
            "owner_approval_status",
            "rotation_required",
            "last_verified_at",
        ]:
            assert field in audit["credentialAuditFields"]
        assert audit["real_credentials_included"] is False
        assert audit["template_only"] is True
        assert len(audit["credentialAuditRows"]) == 10
        for row in audit["credentialAuditRows"]:
            assert row["credential_reference_id"].startswith("vault_ref_")
            assert row["secret_value_present"] is False
            assert row["token_in_git"] is False
            assert row["token_in_runtime_json"] is False
            assert row["env_written_by_agos"] is False
            assert row["logs_contain_secret"] is False
            assert row["screenshots_contain_secret"] is False

        policy = report["secretBoundaryPolicy"]
        assert policy["storagePolicy"]["git_tokens_allowed"] is False
        assert policy["storagePolicy"]["runtime_json_tokens_allowed"] is False
        assert policy["storagePolicy"]["agos_env_writes_allowed"] is False
        assert policy["storagePolicy"]["logs_containing_secrets_allowed"] is False
        assert policy["storagePolicy"]["screenshots_containing_secrets_allowed"] is False
        assert policy["allowedHandlingPolicy"]["external_vault_reference_allowed"] is True
        assert policy["allowedHandlingPolicy"]["operator_runtime_injection_allowed"] is True
        assert policy["allowedHandlingPolicy"]["least_privilege_scopes_required"] is True
        assert policy["allowedHandlingPolicy"]["revocation_support_required"] is True
        assert policy["allowedHandlingPolicy"]["rotation_support_required"] is True
        assert policy["executionBoundary"]["real_platform_api_called"] is False
        assert policy["executionBoundary"]["real_data_ingested"] is False
        assert policy["executionBoundary"]["agos_training_started"] is False

        evidence = report["secretBoundaryEvidence"]
        assert evidence["real_secrets_requested_in_chat"] is False
        assert evidence["real_tokens_stored"] is False
        assert evidence["tokens_in_git_allowed"] is False
        assert evidence["tokens_in_runtime_json_allowed"] is False
        assert evidence["env_writes_by_agos_allowed"] is False
        assert evidence["logs_containing_secrets_allowed"] is False
        assert evidence["screenshots_containing_secrets_allowed"] is False
        assert evidence["real_platform_api_called"] is False
        assert evidence["real_data_ingested"] is False
        assert evidence["agos_training_started"] is False
        assert evidence["write_api_allowed"] is False

        for output_name in [
            "CREDENTIAL_VAULT_CONTRACT.json",
            "SECRET_BOUNDARY_POLICY.json",
            "CREDENTIAL_AUDIT_TEMPLATE.json",
            "SECRET_BOUNDARY_EVIDENCE.json",
        ]:
            path = output_dir / output_name
            assert path.exists(), f"missing output: {output_name}"
            payload = json.loads(path.read_text(encoding="utf-8"))
            serialized = json.dumps(payload, ensure_ascii=False).lower()
            assert "token_value" not in serialized
            assert "access_token" not in serialized
            assert "refresh_token" not in serialized
            assert "client_secret" not in serialized

    print("credential_vault_contract_smoke_test passed")


if __name__ == "__main__":
    main()
