from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.read_only_api_dry_run import ReadOnlyApiDryRun


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp) / "real_data_access"
        report = ReadOnlyApiDryRun(output_dir).build()

        assert report["contract_id"] == "READ_ONLY_API_DRY_RUN_CONTRACT"
        assert report["round_id"] == "ROUND-REALDATA-004_READ_ONLY_API_DRY_RUN"
        assert report["status"] == "dry_run_readiness_defined_no_real_api_calls"

        for mode in ["not_connected", "mock_connection", "read_only_authorized", "blocked"]:
            assert mode in report["connectionModes"]

        for check in [
            "credential reference exists",
            "scope is read-only",
            "rate limit known",
            "cost limit known",
            "API terms reviewed",
            "private data excluded",
            "write actions disabled",
        ]:
            assert check in report["dryRunChecks"]

        for field in [
            "platform_id",
            "endpoint_type",
            "permission_status",
            "allowed_data_types",
            "forbidden_data_types",
            "dry_run_status",
            "blocker_reason",
        ]:
            assert field in report["dryRunOutputShape"]

        safety = report["safetyBoundary"]
        assert safety["write_api_allowed"] is False
        assert safety["auto_publish_allowed"] is False
        assert safety["auto_reply_allowed"] is False
        assert safety["auto_dm_allowed"] is False
        assert safety["large_real_dataset_storage_allowed"] is False
        assert safety["agos_training_allowed"] is False
        assert safety["real_api_called"] is False

        status = report["platformDryRunStatus"]
        assert status["platform_count"] == 3
        assert status["blocked_count"] == 3
        assert status["read_only_authorized_count"] == 0
        assert status["all_write_actions_disabled"] is True
        assert status["all_private_data_excluded"] is True
        assert status["all_training_disabled"] is True
        for platform in status["platformStatuses"]:
            assert platform["connection_mode"] in report["connectionModes"]
            assert platform["credential_reference_exists"] is True
            assert platform["credential_reference_verified"] is False
            assert platform["scope_is_read_only"] is True
            assert platform["rate_limit_known"] is False
            assert platform["cost_limit_known"] is False
            assert platform["api_terms_reviewed"] is False
            assert platform["write_actions_disabled"] is True
            assert platform["dry_run_status"] == "blocked"

        permission_report = report["apiPermissionCheckReport"]
        assert permission_report["check_count"] == 9
        assert permission_report["blocked_permission_count"] == 9
        assert permission_report["write_api_allowed"] is False
        assert permission_report["publish_allowed"] is False
        assert permission_report["reply_allowed"] is False
        assert permission_report["dm_allowed"] is False
        assert permission_report["large_real_dataset_storage_allowed"] is False
        assert permission_report["agos_training_started"] is False
        for item in permission_report["permissionChecks"]:
            assert item["permission_status"] == "blocked"
            assert item["dry_run_status"] == "blocked"
            assert "private messages" in item["forbidden_data_types"]
            assert "large real datasets" in item["forbidden_data_types"]
            assert item["writes_disabled"] is True
            assert item["large_dataset_storage_allowed"] is False
            assert item["training_allowed"] is False

        decision = report["readOnlyApiDryRunDecision"]
        assert decision["gate_decision"] == "blocked_for_live_api"
        assert decision["mock_dry_run_allowed"] is True
        assert decision["read_only_live_dry_run_allowed"] is False
        assert decision["write_api_allowed"] is False
        assert decision["publish_allowed"] is False
        assert decision["reply_allowed"] is False
        assert decision["dm_allowed"] is False
        assert decision["large_real_dataset_storage_allowed"] is False
        assert decision["agos_training_allowed"] is False
        assert decision["real_api_called"] is False

        for output_name in [
            "READ_ONLY_API_DRY_RUN_CONTRACT.json",
            "PLATFORM_DRY_RUN_STATUS.json",
            "API_PERMISSION_CHECK_REPORT.json",
            "READ_ONLY_API_DRY_RUN_DECISION.json",
        ]:
            path = output_dir / output_name
            assert path.exists(), f"missing output: {output_name}"
            json.loads(path.read_text(encoding="utf-8"))

    print("read_only_api_dry_run_smoke_test passed")


if __name__ == "__main__":
    main()
