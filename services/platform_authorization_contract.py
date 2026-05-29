"""Platform authorization contract for controlled real-data access."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.runtime_persistence import utc_now_iso


DEFAULT_OUTPUT_DIR = Path("runtime/real_data_access")

SUPPORTED_MVP_PLATFORMS = ["YouTube", "TikTok", "Instagram"]
OPTIONAL_LATER_PLATFORMS = [
    "X / Twitter",
    "Reddit",
    "Facebook Page",
    "LinkedIn",
    "小红书",
    "抖音",
    "Bilibili",
]
ACCESS_STATUSES = [
    "not_connected",
    "authorization_pending",
    "authorized_read_only",
    "suspended",
    "revoked",
]
REQUIRED_AUTHORIZATION_REQUIREMENTS = [
    "account owner approval",
    "platform API permission scope",
    "read-only access",
    "no private messages",
    "no password storage",
    "no token committed to repo",
]


class PlatformAuthorizationContract:
    """Create local authorization contracts without credentials or API calls."""

    def __init__(self, output_dir: str | Path = DEFAULT_OUTPUT_DIR) -> None:
        self.output_dir = Path(output_dir)
        self.contract_path = self.output_dir / "PLATFORM_AUTHORIZATION_CONTRACT.json"
        self.status_path = self.output_dir / "PLATFORM_AUTHORIZATION_STATUS.json"
        self.scope_path = self.output_dir / "PLATFORM_SCOPE_REQUIREMENTS.json"
        self.evidence_path = self.output_dir / "AUTHORIZATION_EVIDENCE.json"

    def build(self) -> dict[str, Any]:
        created_at = utc_now_iso()
        platform_contracts = [self._platform_contract(platform, "mvp", created_at) for platform in SUPPORTED_MVP_PLATFORMS]
        platform_contracts.extend(
            self._platform_contract(platform, "optional_later", created_at) for platform in OPTIONAL_LATER_PLATFORMS
        )
        status = self._status(platform_contracts, created_at)
        scope = self._scope_requirements(platform_contracts, created_at)
        evidence = self._evidence(platform_contracts, status, scope, created_at)
        contract = {
            "contract_id": "PLATFORM_AUTHORIZATION_CONTRACT",
            "round_id": "ROUND-REALDATA-001_PLATFORM_AUTHORIZATION_CONTRACT",
            "phase": "AGOS_REAL_DATA_CONTROLLED_ACCESS",
            "created_at": created_at,
            "status": "contract_defined_no_connections",
            "supportedMvpPlatforms": SUPPORTED_MVP_PLATFORMS,
            "optionalLaterPlatforms": OPTIONAL_LATER_PLATFORMS,
            "accessStatuses": ACCESS_STATUSES,
            "accountAuthorizationRequirements": REQUIRED_AUTHORIZATION_REQUIREMENTS,
            "platformAuthorizationContracts": platform_contracts,
            "authorizationStatus": status,
            "platformScopeRequirements": scope,
            "authorizationEvidence": evidence,
            "safetyBoundary": {
                "real_platform_api_called": False,
                "credentials_stored": False,
                "env_file_written": False,
                "real_data_ingested": False,
                "agos_training_started": False,
                "password_storage_allowed": False,
                "private_message_access_allowed": False,
                "write_api_allowed": False,
                "token_commit_allowed": False,
            },
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
        self.status_path.write_text(json.dumps(contract["authorizationStatus"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.scope_path.write_text(json.dumps(contract["platformScopeRequirements"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.evidence_path.write_text(json.dumps(contract["authorizationEvidence"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    @staticmethod
    def _platform_contract(platform: str, platform_group: str, created_at: str) -> dict[str, Any]:
        return {
            "platform": platform,
            "platform_group": platform_group,
            "access_status": "not_connected",
            "account_owner_approval_required": True,
            "account_owner_approval_status": "not_requested",
            "required_permission_scope": "read_only_public_analytics_and_public_content_metadata",
            "read_only_access_required": True,
            "private_messages_allowed": False,
            "password_storage_allowed": False,
            "token_committed_to_repo_allowed": False,
            "credential_storage_allowed": False,
            "write_api_allowed": False,
            "auto_post_allowed": False,
            "auto_reply_allowed": False,
            "auto_dm_allowed": False,
            "real_data_ingestion_allowed": False,
            "training_allowed": False,
            "authorization_evidence_required": True,
            "created_at": created_at,
        }

    @staticmethod
    def _status(platform_contracts: list[dict[str, Any]], created_at: str) -> dict[str, Any]:
        platform_statuses = [
            {
                "platform": item["platform"],
                "platform_group": item["platform_group"],
                "access_status": item["access_status"],
                "authorization_pending": False,
                "authorized_read_only": False,
                "owner_approved": False,
                "scope_verified": False,
                "token_present": False,
                "credential_present": False,
                "safe_to_ingest_real_data": False,
                "requires_human_review": True,
            }
            for item in platform_contracts
        ]
        return {
            "status_id": "PLATFORM_AUTHORIZATION_STATUS",
            "round_id": "ROUND-REALDATA-001_PLATFORM_AUTHORIZATION_CONTRACT",
            "created_at": created_at,
            "platformStatuses": platform_statuses,
            "mvp_platform_count": len([item for item in platform_statuses if item["platform_group"] == "mvp"]),
            "authorized_read_only_count": 0,
            "not_connected_count": len(platform_statuses),
            "real_data_access_enabled": False,
            "all_platforms_default_not_connected": all(item["access_status"] == "not_connected" for item in platform_statuses),
        }

    @staticmethod
    def _scope_requirements(platform_contracts: list[dict[str, Any]], created_at: str) -> dict[str, Any]:
        scopes = [
            {
                "platform": item["platform"],
                "platform_group": item["platform_group"],
                "required_scope": item["required_permission_scope"],
                "allowed_operations": [
                    "read public account metadata after owner approval",
                    "read public content metadata after owner approval",
                    "read public analytics if the platform grants read-only scope",
                ],
                "forbidden_operations": [
                    "private messages",
                    "password storage",
                    "token commit",
                    "posting",
                    "replying",
                    "DM",
                    "following",
                    "liking",
                    "write API",
                    "login scraping",
                    "training without later gate",
                ],
                "requires_owner_approval": True,
                "requires_human_review": True,
                "read_only": True,
                "write_allowed": False,
            }
            for item in platform_contracts
        ]
        return {
            "scope_id": "PLATFORM_SCOPE_REQUIREMENTS",
            "round_id": "ROUND-REALDATA-001_PLATFORM_AUTHORIZATION_CONTRACT",
            "created_at": created_at,
            "scopeRequirements": scopes,
            "minimum_scope_policy": "read_only_only",
            "private_message_scope_allowed": False,
            "write_scope_allowed": False,
            "credential_storage_allowed": False,
            "token_commit_allowed": False,
        }

    @staticmethod
    def _evidence(
        platform_contracts: list[dict[str, Any]],
        status: dict[str, Any],
        scope: dict[str, Any],
        created_at: str,
    ) -> dict[str, Any]:
        return {
            "evidence_id": "AUTHORIZATION_EVIDENCE",
            "round_id": "ROUND-REALDATA-001_PLATFORM_AUTHORIZATION_CONTRACT",
            "created_at": created_at,
            "evidence_status": "contract_only_no_real_connections",
            "contract_defined": True,
            "schema_required": True,
            "mvp_platforms_defined": SUPPORTED_MVP_PLATFORMS,
            "optional_later_platforms_defined": OPTIONAL_LATER_PLATFORMS,
            "platform_status_values_defined": ACCESS_STATUSES,
            "account_owner_approval_required": all(item["account_owner_approval_required"] for item in platform_contracts),
            "read_only_access_required": all(item["read_only_access_required"] for item in platform_contracts),
            "private_messages_allowed": False,
            "password_storage_allowed": False,
            "token_committed_to_repo_allowed": False,
            "credentials_found": False,
            "env_file_written": False,
            "real_platform_api_called": False,
            "real_data_ingested": False,
            "agos_training_started": False,
            "real_data_access_enabled": status["real_data_access_enabled"],
            "write_scope_allowed": scope["write_scope_allowed"],
            "next_gate_required": "ROUND-REALDATA-002_READ_ONLY_CONNECTION_DRY_RUN",
        }


if __name__ == "__main__":
    report = PlatformAuthorizationContract().build()
    print(json.dumps(report["authorizationEvidence"], ensure_ascii=True, indent=2, sort_keys=True))
