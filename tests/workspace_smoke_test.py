from __future__ import annotations

import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.workspace_service import WorkspaceNotFoundError, WorkspaceStore
from schemas.workspace_schema import WorkspaceValidationError


def main() -> None:
    root = Path("runtime/test_workspaces")
    if root.exists():
        shutil.rmtree(root)

    store = WorkspaceStore(root)
    alpha = store.create(
        {
            "workspace_id": "alpha_japan",
            "name": "Alpha Japan Workspace",
            "owner": "Alpha Co",
            "product_name": "Japan Guide",
            "industry": "travel",
            "target_markets": ["US", "EU"],
            "status": "active",
            "metadata": {"language": "en"},
        }
    )
    beta = store.create(
        {
            "workspace_id": "beta_saas",
            "name": "Beta SaaS Workspace",
            "owner": "Beta Co",
            "product_name": "Growth SaaS",
            "industry": "software",
            "target_markets": ["JP"],
            "status": "draft",
            "metadata": {"language": "ja"},
        }
    )

    assert store.get("alpha_japan").owner == "Alpha Co"
    assert store.get("beta_saas").owner == "Beta Co"
    assert alpha.workspace_id != beta.workspace_id
    assert len(store.list()) == 2

    try:
        store.get("../escaped")
        raise AssertionError("Path traversal workspace_id was accepted")
    except WorkspaceValidationError:
        pass

    try:
        store.get("missing_workspace")
        raise AssertionError("Missing workspace did not raise")
    except WorkspaceNotFoundError:
        pass

    shutil.rmtree(root)
    print("workspace smoke test passed")


if __name__ == "__main__":
    main()
