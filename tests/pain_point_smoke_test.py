from __future__ import annotations

import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from schemas.pain_point_schema import PainPointValidationError
from services.pain_point_engine import PainPointStore
from services.workspace_service import WorkspaceStore


def main() -> None:
    root = Path("runtime/test_pain_point_workspaces")
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

    store = PainPointStore(workspace_store)
    store.import_many(
        "alpha_japan",
        [
            {
                "pain_point_id": "transit_confusion",
                "source": "local_sample",
                "platform": "reddit",
                "market": "US",
                "audience": "first_time_traveler",
                "category": "transport",
                "title": "Travelers are confused by train transfers",
                "evidence": "Sample users ask how to avoid wrong train transfers.",
                "trend_score": 88,
                "urgency_score": 80,
                "value_score": 92,
                "tags": ["train", "first_trip", "navigation"],
            },
            {
                "pain_point_id": "food_language_gap",
                "source": "local_sample",
                "platform": "seo",
                "market": "US",
                "audience": "family_traveler",
                "category": "food",
                "title": "Families worry about ordering food without Japanese",
                "evidence": "Sample search intent includes English menus and allergy notes.",
                "trend_score": 70,
                "urgency_score": 74,
                "value_score": 82,
                "tags": ["food", "language", "family"],
            },
        ],
    )

    assert len(store.list("alpha_japan")) == 2
    assert len(store.list("alpha_japan", platform="reddit")) == 1
    assert store.top("alpha_japan", limit=1)[0].pain_point_id == "transit_confusion"
    assert store.top("alpha_japan", limit=1)[0].priority_score > store.list("alpha_japan", category="food")[0].priority_score

    try:
        store.upsert(
            {
                "workspace_id": "alpha_japan",
                "pain_point_id": "bad_score",
                "source": "local_sample",
                "platform": "seo",
                "market": "US",
                "audience": "traveler",
                "category": "test",
                "title": "Bad score",
                "evidence": "Should fail",
                "trend_score": 101,
                "urgency_score": 1,
                "value_score": 1,
                "tags": [],
            }
        )
        raise AssertionError("Out-of-range score was accepted")
    except PainPointValidationError:
        pass

    try:
        store.upsert(
            {
                "workspace_id": "alpha_japan",
                "pain_point_id": "bad_platform",
                "source": "local_sample",
                "platform": "wechat",
                "market": "US",
                "audience": "traveler",
                "category": "test",
                "title": "Bad platform",
                "evidence": "Should fail",
                "trend_score": 1,
                "urgency_score": 1,
                "value_score": 1,
                "tags": [],
            }
        )
        raise AssertionError("Unsupported platform was accepted")
    except PainPointValidationError:
        pass

    shutil.rmtree(root)
    print("pain point smoke test passed")


if __name__ == "__main__":
    main()
