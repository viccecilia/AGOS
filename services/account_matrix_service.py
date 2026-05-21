"""Workspace-scoped account matrix service."""

from __future__ import annotations

import json
from pathlib import Path

from models.account_matrix import AccountProfile
from models.workspace import utc_now_iso
from schemas.account_matrix_schema import validate_account_payload
from services.workspace_service import WorkspaceStore


class AccountProfileNotFoundError(KeyError):
    pass


class AccountMatrixStore:
    def __init__(self, workspace_store: WorkspaceStore | None = None) -> None:
        self.workspace_store = workspace_store or WorkspaceStore()

    def upsert(self, payload: dict) -> AccountProfile:
        validate_account_payload(payload)
        workspace_id = str(payload["workspace_id"])
        self.workspace_store.get(workspace_id)
        existing = None
        if self._account_file(workspace_id, str(payload["account_id"])).exists():
            existing = self.get(workspace_id, str(payload["account_id"]))
        account = AccountProfile.from_dict(
            {
                **payload,
                "created_at": existing.created_at if existing else utc_now_iso(),
                "updated_at": utc_now_iso(),
            }
        )
        path = self._account_file(account.workspace_id, account.account_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(account.to_dict(), ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return account

    def get(self, workspace_id: str, account_id: str) -> AccountProfile:
        self.workspace_store.get(workspace_id)
        path = self._account_file(workspace_id, account_id)
        if not path.exists():
            raise AccountProfileNotFoundError(account_id)
        return AccountProfile.from_dict(json.loads(path.read_text(encoding="utf-8")))

    def list(self, workspace_id: str, platform: str | None = None, status: str | None = None) -> list[AccountProfile]:
        self.workspace_store.get(workspace_id)
        root = self._accounts_dir(workspace_id)
        if not root.exists():
            return []
        accounts = [
            AccountProfile.from_dict(json.loads(path.read_text(encoding="utf-8")))
            for path in root.glob("*.json")
        ]
        if platform:
            accounts = [item for item in accounts if item.platform == platform]
        if status:
            accounts = [item for item in accounts if item.status == status]
        return sorted(accounts, key=lambda item: (item.platform, item.account_id))

    def _accounts_dir(self, workspace_id: str) -> Path:
        workspace_file = self.workspace_store._workspace_file(workspace_id)
        return workspace_file.parent / "accounts"

    def _account_file(self, workspace_id: str, account_id: str) -> Path:
        validate_account_payload(
            {
                "workspace_id": workspace_id,
                "account_id": account_id,
                "platform": "seo",
                "handle": "placeholder",
                "display_name": "placeholder",
            }
        )
        return self._accounts_dir(workspace_id) / f"{account_id}.json"
