"""Local platform credential vault with workspace isolation."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from pathlib import Path
from typing import Any

from services.runtime_persistence import utc_now_iso


CREDENTIAL_TYPES = {"api_key", "oauth_token", "refresh_token"}
DEFAULT_VAULT_ROOT = Path("runtime/platform_credentials")


class PlatformCredentialVault:
    """Store platform API credentials locally without exposing plaintext in reports."""

    def __init__(self, root: str | Path = DEFAULT_VAULT_ROOT, master_secret: str | None = None) -> None:
        self.root = Path(root)
        self.master_secret = master_secret or os.environ.get("AGOS_LOCAL_VAULT_SECRET") or "AGOS_LOCAL_DEV_ONLY_SECRET"
        self.status_path = self.root / "VAULT_STATUS.json"
        self.feed_path = self.root / "credential_vault_feed.json"

    def store_credential(
        self,
        workspace_id: str,
        platform: str,
        credential_type: str,
        value: str,
        scopes: list[str] | None = None,
    ) -> dict[str, Any]:
        self._validate(workspace_id, platform, credential_type, value)
        vault = self._load_workspace_vault(workspace_id)
        credential_id = self._credential_id(workspace_id, platform, credential_type)
        payload = {
            "credential_id": credential_id,
            "workspace_id": workspace_id,
            "platform": platform,
            "credential_type": credential_type,
            "workspace_scope": scopes or [workspace_id],
            "sealed_value": self._seal(workspace_id, platform, credential_type, value),
            "fingerprint": self._fingerprint(value),
            "created_at": utc_now_iso(),
            "updated_at": utc_now_iso(),
            "storage": "local_only",
            "plaintext_logged": False,
            "git_safe": False,
        }
        vault[credential_id] = payload
        self._save_workspace_vault(workspace_id, vault)
        return self._redact(payload)

    def get_credential(self, workspace_id: str, platform: str, credential_type: str) -> str:
        credential_id = self._credential_id(workspace_id, platform, credential_type)
        payload = self._load_workspace_vault(workspace_id).get(credential_id)
        if not payload:
            raise KeyError(credential_id)
        return self._unseal(workspace_id, platform, credential_type, payload["sealed_value"])

    def delete_credential(self, workspace_id: str, platform: str, credential_type: str) -> None:
        credential_id = self._credential_id(workspace_id, platform, credential_type)
        vault = self._load_workspace_vault(workspace_id)
        vault.pop(credential_id, None)
        self._save_workspace_vault(workspace_id, vault)

    def status(self) -> dict[str, Any]:
        workspaces = []
        for workspace_dir in sorted(self.root.glob("workspace_*")):
            if not workspace_dir.is_dir():
                continue
            workspace_id = workspace_dir.name.removeprefix("workspace_")
            vault = self._load_workspace_vault(workspace_id)
            workspaces.append(
                {
                    "workspace_id": workspace_id,
                    "credential_count": len(vault),
                    "platforms": sorted({item["platform"] for item in vault.values()}),
                    "credential_types": sorted({item["credential_type"] for item in vault.values()}),
                    "fingerprints": sorted(item["fingerprint"] for item in vault.values()),
                    "storage": "local_only",
                    "plaintext_exposed": False,
                    "workspace_isolated": True,
                }
            )
        report = {
            "report_id": "PLATFORM_CREDENTIAL_VAULT_STATUS",
            "created_at": utc_now_iso(),
            "status": "vault_ready",
            "scope": "local_workspace_isolated_credentials_only",
            "workspaceCredentialStatus": workspaces,
            "credentialVaultFeed": self._feed(workspaces),
            "credentialVaultSummary": {
                "workspaces": len(workspaces),
                "credentials": sum(item["credential_count"] for item in workspaces),
                "workspace_isolation_enabled": True,
                "plaintext_logging_enabled": False,
                "public_upload_allowed": False,
                "git_commit_allowed": False,
            },
            "safetyBoundary": "Credential values are local-only and redacted from reports. Do not commit vault.json files or print plaintext values.",
        }
        self.root.mkdir(parents=True, exist_ok=True)
        self.status_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.feed_path.write_text(json.dumps(report["credentialVaultFeed"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        return report

    def bootstrap_sample_status(self) -> dict[str, Any]:
        if not self._load_workspace_vault("JAG-LAB"):
            self.store_credential("JAG-LAB", "Reddit", "api_key", "sample_local_only_reddit_key", ["read_public"])
            self.store_credential("JAG-LAB", "YouTube", "oauth_token", "sample_local_only_youtube_token", ["analytics.readonly"])
        if not self._load_workspace_vault("JAG-PROD"):
            self.store_credential("JAG-PROD", "Instagram", "refresh_token", "sample_local_only_instagram_refresh", ["account_analytics"])
        return self.status()

    @staticmethod
    def _redact(payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "credential_id": payload["credential_id"],
            "workspace_id": payload["workspace_id"],
            "platform": payload["platform"],
            "credential_type": payload["credential_type"],
            "workspace_scope": payload["workspace_scope"],
            "fingerprint": payload["fingerprint"],
            "created_at": payload["created_at"],
            "updated_at": payload["updated_at"],
            "storage": payload["storage"],
            "plaintext_exposed": False,
        }

    @staticmethod
    def _credential_id(workspace_id: str, platform: str, credential_type: str) -> str:
        token = f"{workspace_id}:{platform}:{credential_type}".lower().replace(" ", "_")
        digest = hashlib.sha256(token.encode("utf-8")).hexdigest()[:12]
        return f"cred_{digest}"

    @staticmethod
    def _workspace_dir_name(workspace_id: str) -> str:
        safe = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in workspace_id)
        return f"workspace_{safe}"

    def _workspace_path(self, workspace_id: str) -> Path:
        return self.root / self._workspace_dir_name(workspace_id) / "vault.json"

    def _load_workspace_vault(self, workspace_id: str) -> dict[str, Any]:
        path = self._workspace_path(workspace_id)
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    def _save_workspace_vault(self, workspace_id: str, vault: dict[str, Any]) -> None:
        path = self._workspace_path(workspace_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(vault, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    def _seal(self, workspace_id: str, platform: str, credential_type: str, value: str) -> str:
        key = self._key_stream(workspace_id, platform, credential_type, len(value.encode("utf-8")))
        sealed = bytes(byte ^ key[index] for index, byte in enumerate(value.encode("utf-8")))
        return base64.urlsafe_b64encode(sealed).decode("ascii")

    def _unseal(self, workspace_id: str, platform: str, credential_type: str, sealed_value: str) -> str:
        sealed = base64.urlsafe_b64decode(sealed_value.encode("ascii"))
        key = self._key_stream(workspace_id, platform, credential_type, len(sealed))
        value = bytes(byte ^ key[index] for index, byte in enumerate(sealed))
        return value.decode("utf-8")

    def _key_stream(self, workspace_id: str, platform: str, credential_type: str, length: int) -> bytes:
        seed = f"{workspace_id}:{platform}:{credential_type}".encode("utf-8")
        output = b""
        counter = 0
        while len(output) < length:
            msg = seed + counter.to_bytes(4, "big")
            output += hmac.new(self.master_secret.encode("utf-8"), msg, hashlib.sha256).digest()
            counter += 1
        return output[:length]

    @staticmethod
    def _fingerprint(value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]

    @staticmethod
    def _validate(workspace_id: str, platform: str, credential_type: str, value: str) -> None:
        if not workspace_id:
            raise ValueError("workspace_id is required")
        if not platform:
            raise ValueError("platform is required")
        if credential_type not in CREDENTIAL_TYPES:
            raise ValueError(f"Unsupported credential type: {credential_type}")
        if not value:
            raise ValueError("credential value is required")

    @staticmethod
    def _feed(workspaces: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "time": utc_now_iso(),
                "workspace_id": item["workspace_id"],
                "credential_count": item["credential_count"],
                "platforms": item["platforms"],
                "credential_types": item["credential_types"],
                "storage": item["storage"],
                "workspace_isolated": item["workspace_isolated"],
                "plaintext_exposed": item["plaintext_exposed"],
            }
            for item in workspaces
        ]


if __name__ == "__main__":
    result = PlatformCredentialVault().status()
    print(json.dumps({"status": result["status"], "workspaces": result["credentialVaultSummary"]["workspaces"]}, indent=2))
