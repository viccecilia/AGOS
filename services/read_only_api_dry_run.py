"""Read-only API dry-run readiness contract without platform access."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.runtime_persistence import utc_now_iso


DEFAULT_OUTPUT_DIR = Path("runtime/real_data_access")
MVP_PLATFORM_IDS = ["youtube", "tiktok", "instagram"]
CONNECTION_MODES = ["not_connected", "mock_connection", "read_only_authorized", "blocked"]
ENDPOINT_TYPES = ["trend_search", "public_content_metadata", "public_analytics"]
ALLOWED_DATA_TYPES = [
    "public trend metadata after authorization",
    "public content metadata after authorization",
    "public engagement metrics after authorization",
]
FORBIDDEN_DATA_TYPES = [
    "private messages",
    "private account data",
    "sensitive personal data",
    "raw credential values",
    "write action payloads",
    "large real datasets",
]


class ReadOnlyApiDryRun:
    """Create API dry-run readiness artifacts without calling real APIs."""

    def __init__(self, output_dir: str | Path = DEFAULT_OUTPUT_DIR) -> None:
        self.output_dir = Path(output_dir)
        self.contract_path = self.output_dir / "READ_ONLY_API_DRY_RUN_CONTRACT.json"
        self.status_path = self.output_dir / "PLATFORM_DRY_RUN_STATUS.json"
        self.permission_path = self.output_dir / "API_PERMISSION_CHECK_REPORT.json"
        self.decision_path = self.output_dir / "READ_ONLY_API_DRY_RUN_DECISION.json"

    def build(self) -> dict[str, Any]:
        created_at = utc_now_iso()
        platform_status = self._platform_status(created_at)
        permission_report = self._permission_report(platform_status, created_at)
        decision = self._decision(platform_status, permission_report, created_at)
        contract = {
            "contract_id": "READ_ONLY_API_DRY_RUN_CONTRACT",
            "round_id": "ROUND-REALDATA-004_READ_ONLY_API_DRY_RUN",
            "phase": "AGOS_REAL_DATA_CONTROLLED_ACCESS",
            "created_at": created_at,
            "status": "dry_run_readiness_defined_no_real_api_calls",
            "supportedPlatformIds": MVP_PLATFORM_IDS,
            "connectionModes": CONNECTION_MODES,
            "endpointTypes": ENDPOINT_TYPES,
            "dryRunChecks": [
                "credential reference exists",
                "scope is read-only",
                "rate limit known",
                "cost limit known",
                "API terms reviewed",
                "private data excluded",
                "write actions disabled",
            ],
            "dryRunOutputShape": [
                "platform_id",
                "endpoint_type",
                "permission_status",
                "allowed_data_types",
                "forbidden_data_types",
                "dry_run_status",
                "blocker_reason",
            ],
            "safetyBoundary": {
                "write_api_allowed": False,
                "auto_publish_allowed": False,
                "auto_reply_allowed": False,
                "auto_dm_allowed": False,
                "large_real_dataset_storage_allowed": False,
                "agos_training_allowed": False,
                "real_api_called": False,
                "mock_connection_only": True,
            },
            "platformDryRunStatus": platform_status,
            "apiPermissionCheckReport": permission_report,
            "readOnlyApiDryRunDecision": decision,
        }
        self.persist(contract)
        return contract

    def state(self) -> dict[str, Any]:
        if self.contract_path.exists():
            return json.loads(self.contract_path.read_text(encoding="utf-8"))
        return self.build()

    def persist(self, contract: dict[str, Any]) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.contract_path.write_text(json.dumps(contract, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.status_path.write_text(json.dumps(contract["platformDryRunStatus"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.permission_path.write_text(json.dumps(contract["apiPermissionCheckReport"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.decision_path.write_text(json.dumps(contract["readOnlyApiDryRunDecision"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    @staticmethod
    def _platform_status(created_at: str) -> dict[str, Any]:
        statuses = []
        for platform_id in MVP_PLATFORM_IDS:
            statuses.append(
                {
                    "platform_id": platform_id,
                    "connection_mode": "not_connected",
                    "credential_reference_exists": True,
                    "credential_reference_verified": False,
                    "owner_approval_status": "not_requested",
                    "scope_is_read_only": True,
                    "rate_limit_known": False,
                    "cost_limit_known": False,
                    "api_terms_reviewed": False,
                    "private_data_excluded": True,
                    "write_actions_disabled": True,
                    "large_dataset_storage_disabled": True,
                    "training_disabled": True,
                    "dry_run_status": "blocked",
                    "blocker_reason": "owner approval, verified credential reference, rate limit, cost limit, and API terms review are still pending",
                }
            )
        return {
            "status_id": "PLATFORM_DRY_RUN_STATUS",
            "round_id": "ROUND-REALDATA-004_READ_ONLY_API_DRY_RUN",
            "created_at": created_at,
            "connectionModes": CONNECTION_MODES,
            "platformStatuses": statuses,
            "platform_count": len(statuses),
            "mock_connection_ready_count": 0,
            "read_only_authorized_count": 0,
            "blocked_count": len(statuses),
            "all_write_actions_disabled": all(item["write_actions_disabled"] for item in statuses),
            "all_private_data_excluded": all(item["private_data_excluded"] for item in statuses),
            "all_training_disabled": all(item["training_disabled"] for item in statuses),
        }

    @staticmethod
    def _permission_report(platform_status: dict[str, Any], created_at: str) -> dict[str, Any]:
        checks = []
        for platform in platform_status["platformStatuses"]:
            for endpoint_type in ENDPOINT_TYPES:
                checks.append(
                    {
                        "platform_id": platform["platform_id"],
                        "endpoint_type": endpoint_type,
                        "permission_status": "blocked",
                        "connection_mode": platform["connection_mode"],
                        "allowed_data_types": ALLOWED_DATA_TYPES,
                        "forbidden_data_types": FORBIDDEN_DATA_TYPES,
                        "dry_run_status": "blocked",
                        "blocker_reason": platform["blocker_reason"],
                        "checks": {
                            "credential_reference_exists": platform["credential_reference_exists"],
                            "credential_reference_verified": platform["credential_reference_verified"],
                            "scope_is_read_only": platform["scope_is_read_only"],
                            "rate_limit_known": platform["rate_limit_known"],
                            "cost_limit_known": platform["cost_limit_known"],
                            "api_terms_reviewed": platform["api_terms_reviewed"],
                            "private_data_excluded": platform["private_data_excluded"],
                            "write_actions_disabled": platform["write_actions_disabled"],
                        },
                        "writes_disabled": True,
                        "large_dataset_storage_allowed": False,
                        "training_allowed": False,
                    }
                )
        return {
            "report_id": "API_PERMISSION_CHECK_REPORT",
            "round_id": "ROUND-REALDATA-004_READ_ONLY_API_DRY_RUN",
            "created_at": created_at,
            "permissionChecks": checks,
            "check_count": len(checks),
            "blocked_permission_count": len(checks),
            "read_only_authorized_permission_count": 0,
            "write_api_allowed": False,
            "publish_allowed": False,
            "reply_allowed": False,
            "dm_allowed": False,
            "large_real_dataset_storage_allowed": False,
            "agos_training_started": False,
        }

    @staticmethod
    def _decision(platform_status: dict[str, Any], permission_report: dict[str, Any], created_at: str) -> dict[str, Any]:
        return {
            "decision_id": "READ_ONLY_API_DRY_RUN_DECISION",
            "round_id": "ROUND-REALDATA-004_READ_ONLY_API_DRY_RUN",
            "created_at": created_at,
            "gate_decision": "blocked_for_live_api",
            "mock_dry_run_allowed": True,
            "read_only_live_dry_run_allowed": False,
            "reason": "No platform is read_only_authorized; owner approval, verified credential references, rate limits, cost limits, and API terms review are pending.",
            "platform_count": platform_status["platform_count"],
            "blocked_platform_count": platform_status["blocked_count"],
            "permission_check_count": permission_report["check_count"],
            "blocked_permission_count": permission_report["blocked_permission_count"],
            "allowed_actions": ["local contract review", "mock connection readiness review", "manual policy verification"],
            "blocked_actions": ["write API", "publish", "reply", "DM", "large real dataset storage", "AGOS training"],
            "write_api_allowed": False,
            "publish_allowed": False,
            "reply_allowed": False,
            "dm_allowed": False,
            "large_real_dataset_storage_allowed": False,
            "agos_training_allowed": False,
            "real_api_called": False,
            "next_gate_required": "ROUND-REALDATA-005_SUPERVISED_READ_ONLY_SAMPLE_RUN",
        }


if __name__ == "__main__":
    report = ReadOnlyApiDryRun().build()
    print(json.dumps(report["readOnlyApiDryRunDecision"], ensure_ascii=True, indent=2, sort_keys=True))
