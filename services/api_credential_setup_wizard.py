"""API credential setup wizard with local-only, workspace-isolated status."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from services.api_capability_registry import PLATFORMS
from services.platform_credential_vault import CREDENTIAL_TYPES, PlatformCredentialVault
from services.runtime_persistence import utc_now_iso


DEFAULT_ROOT = Path("runtime/api_credentials")
SUPPORTED_CREDENTIAL_TYPES = ("api_key", "oauth_token", "refresh_token")


class APICredentialSetupWizard:
    """Guide API credential setup without exposing plaintext in reports or logs."""

    def __init__(
        self,
        root: str | Path = DEFAULT_ROOT,
        vault: PlatformCredentialVault | None = None,
    ) -> None:
        self.root = Path(root)
        self.vault = vault or PlatformCredentialVault()
        self.report_path = self.root / "API_CREDENTIAL_SETUP_WIZARD_REPORT.json"
        self.status_path = self.root / "credential_setup_status.json"
        self.feed_path = self.root / "credential_setup_feed.json"
        self.summary_path = self.root / "credential_setup_summary.json"
        self.gitignore_path = self.root / ".gitignore"
        self._configured_status: list[dict[str, Any]] = []

    def build(self, workspace_id: str = "JAG-LAB") -> dict[str, Any]:
        configured_status = self._load_configured_status(workspace_id)
        setup_steps = self._setup_steps()
        platform_status = [
            self._platform_status(platform, workspace_id, configured_status)
            for platform in PLATFORMS
        ]
        feed = self._feed(platform_status, configured_status)
        summary = self._summary(platform_status, configured_status)
        report = {
            "report_id": "API_CREDENTIAL_SETUP_WIZARD",
            "created_at": utc_now_iso(),
            "status": "credential_setup_wizard_ready",
            "scope": "controlled_api_intelligence_collection",
            "supportedCredentialTypes": list(SUPPORTED_CREDENTIAL_TYPES),
            "credentialSetupSteps": setup_steps,
            "credentialSetupStatus": platform_status,
            "configuredCredentialStatus": configured_status,
            "credentialSetupFeed": feed,
            "credentialSetupSummary": summary,
            "safetyBoundary": "API Credential Setup Wizard stores credentials locally through PlatformCredentialVault, shows only redacted status, keeps workspace scopes isolated, and never enables public upload, Git commit, plaintext logs, or write-side platform automation.",
        }
        self.persist(report)
        return report

    def configure(
        self,
        workspace_id: str,
        platform: str,
        credential_type: str,
        secret_value: str,
        scopes: list[str] | None = None,
    ) -> dict[str, Any]:
        """Store a credential through the vault and return redacted setup status."""

        if credential_type not in CREDENTIAL_TYPES:
            raise ValueError(f"Unsupported credential type: {credential_type}")
        redacted = self.vault.store_credential(
            workspace_id=workspace_id,
            platform=platform,
            credential_type=credential_type,
            value=secret_value,
            scopes=scopes or [f"{workspace_id}:{platform.lower()}:read_only"],
        )
        status = {
            "credential_setup_id": self._setup_id(workspace_id, platform, credential_type),
            "workspace_id": workspace_id,
            "platform": platform,
            "credential_type": credential_type,
            "workspace_scope": redacted["workspace_scope"],
            "status": "configured_locally",
            "storage_mode": "local_vault_only",
            "secret_redacted": True,
            "secret_fingerprint": self._fingerprint(secret_value),
            "plaintext_logged": False,
            "git_commit_allowed": False,
            "public_upload_allowed": False,
            "write_permission": False,
            "configured_at": utc_now_iso(),
        }
        workspace_status = self._load_configured_status(workspace_id)
        workspace_status.append(status)
        self._save_configured_status(workspace_id, workspace_status)
        return status

    def persist(self, report: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self._ensure_gitignore()
        self.report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.status_path.write_text(json.dumps(report["credentialSetupStatus"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.feed_path.write_text(json.dumps(report["credentialSetupFeed"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.summary_path.write_text(json.dumps(report["credentialSetupSummary"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    def _load_configured_status(self, workspace_id: str) -> list[dict[str, Any]]:
        status_path = self._workspace_status_path(workspace_id)
        if not status_path.exists():
            return []
        return json.loads(status_path.read_text(encoding="utf-8"))

    def _save_configured_status(self, workspace_id: str, status: list[dict[str, Any]]) -> None:
        path = self._workspace_status_path(workspace_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_gitignore()
        path.write_text(json.dumps(status, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    def _workspace_status_path(self, workspace_id: str) -> Path:
        safe = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in workspace_id)
        return self.root / f"workspace_{safe}" / "credential_setup_status.redacted.json"

    def _ensure_gitignore(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.gitignore_path.write_text(
            "\n".join(
                [
                    "*",
                    "!.gitignore",
                    "!API_CREDENTIAL_SETUP_WIZARD_REPORT.json",
                    "!credential_setup_status.json",
                    "!credential_setup_feed.json",
                    "!credential_setup_summary.json",
                    "",
                ]
            ),
            encoding="utf-8",
        )

    @staticmethod
    def _setup_steps() -> list[dict[str, Any]]:
        return [
            {
                "step_id": "CRED-STEP-001",
                "name": "Enter credential locally",
                "supported_types": list(SUPPORTED_CREDENTIAL_TYPES),
                "plaintext_logging_enabled": False,
                "public_upload_allowed": False,
            },
            {
                "step_id": "CRED-STEP-002",
                "name": "Seal into local vault",
                "storage_mode": "local_vault_only",
                "git_commit_allowed": False,
            },
            {
                "step_id": "CRED-STEP-003",
                "name": "Publish redacted status",
                "secret_redacted": True,
                "workspace_isolation_enabled": True,
            },
        ]

    @staticmethod
    def _platform_status(
        platform: str,
        workspace_id: str,
        configured_status: list[dict[str, Any]],
    ) -> dict[str, Any]:
        configured_types = sorted(
            {
                item["credential_type"]
                for item in configured_status
                if item["platform"] == platform and item["workspace_id"] == workspace_id
            }
        )
        return {
            "platform": platform,
            "workspace_id": workspace_id,
            "supported_credential_types": list(SUPPORTED_CREDENTIAL_TYPES),
            "configured_credential_types": configured_types,
            "setup_status": "configured_locally" if configured_types else "pending_local_setup",
            "storage_mode": "local_vault_only",
            "workspace_scope": f"{workspace_id}:{platform.lower()}:read_only",
            "secret_redacted": True,
            "plaintext_logged": False,
            "git_commit_allowed": False,
            "public_upload_allowed": False,
            "write_permission": False,
            "requires_human_setup": not bool(configured_types),
        }

    @staticmethod
    def _feed(
        platform_status: list[dict[str, Any]],
        configured_status: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        configured_feed = [
            {
                "time": item["configured_at"],
                "platform": item["platform"],
                "workspace_id": item["workspace_id"],
                "credential_type": item["credential_type"],
                "setup_status": item["status"],
                "storage_mode": item["storage_mode"],
                "workspace_scope": " / ".join(item["workspace_scope"]),
                "secret_redacted": item["secret_redacted"],
                "plaintext_logged": item["plaintext_logged"],
                "git_commit_allowed": item["git_commit_allowed"],
                "public_upload_allowed": item["public_upload_allowed"],
            }
            for item in configured_status
        ]
        pending_feed = [
            {
                "time": utc_now_iso(),
                "platform": item["platform"],
                "workspace_id": item["workspace_id"],
                "credential_type": " / ".join(item["supported_credential_types"]),
                "setup_status": item["setup_status"],
                "storage_mode": item["storage_mode"],
                "workspace_scope": item["workspace_scope"],
                "secret_redacted": item["secret_redacted"],
                "plaintext_logged": item["plaintext_logged"],
                "git_commit_allowed": item["git_commit_allowed"],
                "public_upload_allowed": item["public_upload_allowed"],
            }
            for item in platform_status
            if item["setup_status"] == "pending_local_setup"
        ]
        return configured_feed + pending_feed

    @staticmethod
    def _summary(
        platform_status: list[dict[str, Any]],
        configured_status: list[dict[str, Any]],
    ) -> dict[str, Any]:
        return {
            "wizard_ready": True,
            "platforms": len(platform_status),
            "configured_credentials": len(configured_status),
            "pending_platforms": len([item for item in platform_status if item["setup_status"] == "pending_local_setup"]),
            "supported_credential_types": list(SUPPORTED_CREDENTIAL_TYPES),
            "workspace_isolation_enabled": True,
            "local_storage_only": True,
            "plaintext_logging_enabled": False,
            "public_upload_allowed": False,
            "git_commit_allowed": False,
            "write_permission_default": False,
        }

    @staticmethod
    def _setup_id(workspace_id: str, platform: str, credential_type: str) -> str:
        raw = f"{workspace_id}:{platform}:{credential_type}".lower().encode("utf-8")
        return f"setup_{hashlib.sha256(raw).hexdigest()[:12]}"

    @staticmethod
    def _fingerprint(secret_value: str) -> str:
        return hashlib.sha256(secret_value.encode("utf-8")).hexdigest()[:16]


if __name__ == "__main__":
    result = APICredentialSetupWizard().build()
    print(json.dumps({"status": result["status"], "types": result["supportedCredentialTypes"]}, indent=2))
