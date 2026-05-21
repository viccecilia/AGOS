from __future__ import annotations

import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from schemas.learning_schema import LearningValidationError
from services.learning_engine import LearningEventStore
from services.workspace_service import WorkspaceStore


def main() -> None:
    root = Path("runtime/test_learning_workspaces")
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

    store = LearningEventStore(workspace_store)
    store.record({"event_id": "ev_saved", "workspace_id": "alpha_japan", "target_type": "content_draft", "target_id": "draft_a", "signal": "saved", "weight": 20})
    store.record({"event_id": "ev_converted", "workspace_id": "alpha_japan", "target_type": "content_draft", "target_id": "draft_a", "signal": "converted", "weight": 60})
    store.record({"event_id": "ev_ignored", "workspace_id": "alpha_japan", "target_type": "content_draft", "target_id": "draft_b", "signal": "ignored", "weight": -30})

    recommendations = store.recommendations("alpha_japan")
    assert recommendations[0]["target_id"] == "draft_a"
    assert recommendations[0]["score"] == 80
    assert recommendations[-1]["target_id"] == "draft_b"

    try:
        store.record({"event_id": "bad", "workspace_id": "alpha_japan", "target_type": "content_draft", "target_id": "draft", "signal": "private_data", "weight": 1})
        raise AssertionError("Invalid signal was accepted")
    except LearningValidationError:
        pass

    shutil.rmtree(root)
    print("learning smoke test passed")


if __name__ == "__main__":
    main()
