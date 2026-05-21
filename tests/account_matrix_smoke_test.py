from __future__ import annotations

import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from schemas.account_matrix_schema import AccountMatrixValidationError
from services.account_matrix_service import AccountMatrixStore
from services.workspace_service import WorkspaceNotFoundError, WorkspaceStore


def main() -> None:
    root = Path("runtime/test_account_matrix_workspaces")
    if root.exists():
        shutil.rmtree(root)

    workspace_store = WorkspaceStore(root)
    workspace_store.create(
        {
            "workspace_id": "alpha_japan",
            "name": "Alpha Japan Workspace",
            "owner": "Alpha Co",
            "product_name": "Japan Guide",
            "industry": "travel",
            "target_markets": ["US"],
            "status": "active",
        }
    )

    store = AccountMatrixStore(workspace_store)
    store.upsert(
        {
            "workspace_id": "alpha_japan",
            "account_id": "alpha_tiktok",
            "platform": "tiktok",
            "handle": "@alpha_japan",
            "display_name": "Alpha Japan",
            "status": "active",
            "content_strategy": "Short practical travel tips.",
            "risk_status": "normal",
            "notes": "Use friendly travel guidance tone.",
        }
    )
    store.upsert(
        {
            "workspace_id": "alpha_japan",
            "account_id": "alpha_reddit",
            "platform": "reddit",
            "handle": "u/alpha_japan",
            "display_name": "Alpha Japan Guide",
            "status": "needs_review",
            "content_strategy": "Answer questions without hard selling.",
            "risk_status": "watch",
            "notes": "Manual review required.",
        }
    )

    assert len(store.list("alpha_japan")) == 2
    assert len(store.list("alpha_japan", platform="tiktok")) == 1
    assert len(store.list("alpha_japan", status="needs_review")) == 1
    assert store.get("alpha_japan", "alpha_tiktok").content_strategy.startswith("Short")

    try:
        store.upsert(
            {
                "workspace_id": "alpha_japan",
                "account_id": "bad_platform",
                "platform": "wechat",
                "handle": "bad",
                "display_name": "Bad",
            }
        )
        raise AssertionError("Unsupported platform was accepted")
    except AccountMatrixValidationError:
        pass

    try:
        store.upsert(
            {
                "workspace_id": "alpha_japan",
                "account_id": "secret_account",
                "platform": "x",
                "handle": "@secret",
                "display_name": "Secret",
                "metadata": {"token": "must-not-store"},
            }
        )
        raise AssertionError("Sensitive metadata was accepted")
    except AccountMatrixValidationError:
        pass

    try:
        store.list("missing_workspace")
        raise AssertionError("Missing workspace was accepted")
    except WorkspaceNotFoundError:
        pass

    shutil.rmtree(root)
    print("account matrix smoke test passed")


if __name__ == "__main__":
    main()
