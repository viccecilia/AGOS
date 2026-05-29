from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.platform_authorization_contract import PlatformAuthorizationContract


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp) / "real_data_access"
        report = PlatformAuthorizationContract(output_dir).build()

        assert report["contract_id"] == "PLATFORM_AUTHORIZATION_CONTRACT"
        assert report["round_id"] == "ROUND-REALDATA-001_PLATFORM_AUTHORIZATION_CONTRACT"
        assert report["phase"] == "AGOS_REAL_DATA_CONTROLLED_ACCESS"
        assert report["supportedMvpPlatforms"] == ["YouTube", "TikTok", "Instagram"]
        assert "X / Twitter" in report["optionalLaterPlatforms"]
        assert "小红书" in report["optionalLaterPlatforms"]
        assert "Bilibili" in report["optionalLaterPlatforms"]

        expected_statuses = {
            "not_connected",
            "authorization_pending",
            "authorized_read_only",
            "suspended",
            "revoked",
        }
        assert expected_statuses.issubset(set(report["accessStatuses"]))

        requirements = set(report["accountAuthorizationRequirements"])
        for requirement in [
            "account owner approval",
            "platform API permission scope",
            "read-only access",
            "no private messages",
            "no password storage",
            "no token committed to repo",
        ]:
            assert requirement in requirements

        contracts = report["platformAuthorizationContracts"]
        assert len(contracts) == 10
        assert all(item["access_status"] == "not_connected" for item in contracts)
        assert all(item["account_owner_approval_required"] is True for item in contracts)
        assert all(item["read_only_access_required"] is True for item in contracts)
        assert all(item["private_messages_allowed"] is False for item in contracts)
        assert all(item["password_storage_allowed"] is False for item in contracts)
        assert all(item["token_committed_to_repo_allowed"] is False for item in contracts)
        assert all(item["write_api_allowed"] is False for item in contracts)
        assert all(item["real_data_ingestion_allowed"] is False for item in contracts)
        assert all(item["training_allowed"] is False for item in contracts)

        status = report["authorizationStatus"]
        assert status["real_data_access_enabled"] is False
        assert status["all_platforms_default_not_connected"] is True
        assert status["authorized_read_only_count"] == 0
        assert all(item["token_present"] is False for item in status["platformStatuses"])
        assert all(item["credential_present"] is False for item in status["platformStatuses"])

        scope = report["platformScopeRequirements"]
        assert scope["minimum_scope_policy"] == "read_only_only"
        assert scope["private_message_scope_allowed"] is False
        assert scope["write_scope_allowed"] is False
        assert scope["credential_storage_allowed"] is False
        assert scope["token_commit_allowed"] is False

        evidence = report["authorizationEvidence"]
        assert evidence["contract_defined"] is True
        assert evidence["credentials_found"] is False
        assert evidence["env_file_written"] is False
        assert evidence["real_platform_api_called"] is False
        assert evidence["real_data_ingested"] is False
        assert evidence["agos_training_started"] is False

        safety = report["safetyBoundary"]
        assert safety["real_platform_api_called"] is False
        assert safety["credentials_stored"] is False
        assert safety["env_file_written"] is False
        assert safety["real_data_ingested"] is False
        assert safety["agos_training_started"] is False
        assert safety["write_api_allowed"] is False

        for output_name in [
            "PLATFORM_AUTHORIZATION_CONTRACT.json",
            "PLATFORM_AUTHORIZATION_STATUS.json",
            "PLATFORM_SCOPE_REQUIREMENTS.json",
            "AUTHORIZATION_EVIDENCE.json",
        ]:
            path = output_dir / output_name
            assert path.exists(), f"missing output: {output_name}"
            json.loads(path.read_text(encoding="utf-8"))

    print("platform_authorization_contract_smoke_test passed")


if __name__ == "__main__":
    main()
