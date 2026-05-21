from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.workspace_service import WorkspaceStore


def load_sample(name: str) -> dict:
    return json.loads((PROJECT_ROOT / "runtime" / "samples" / name).read_text(encoding="utf-8"))


def main() -> None:
    korea = load_sample("korea_user_profile.json")
    taiwan = load_sample("taiwan_user_profile.json")
    assert taiwan["workspace_id"] == "taiwan_growth_lab"
    assert taiwan["localization_rules"]["language"] == "zh-Hant"
    assert "Simplified Chinese tone" in taiwan["localization_rules"]["avoid"]

    root = Path("runtime/test_taiwan_profile_workspaces")
    if root.exists():
        shutil.rmtree(root)

    workspace_store = WorkspaceStore(root)
    workspace_store.create(
        {
            "workspace_id": korea["workspace_id"],
            "name": "Korea Guard Workspace",
            "owner": "AGOS",
            "product_name": "AI Growth Operating System",
            "industry": "travel_growth",
            "target_markets": korea["markets"],
            "status": "active",
            "metadata": {"guard": "must_not_be_overwritten"},
        }
    )
    tw_workspace = workspace_store.create(
        {
            "workspace_id": taiwan["workspace_id"],
            "name": "Taiwan Growth Lab",
            "owner": "AGOS",
            "product_name": "AI Growth Operating System",
            "industry": "travel_growth",
            "target_markets": taiwan["markets"],
            "status": "active",
            "metadata": {
                "profile_id": taiwan["profile_id"],
                "primary_personas": taiwan["primary_personas"],
                "localization_rules": taiwan["localization_rules"],
            },
        }
    )

    assert tw_workspace.target_markets == ["TW"]
    assert tw_workspace.metadata["primary_personas"][0]["language_preference"] == "Traditional Chinese"
    assert "family_route_planning" in tw_workspace.metadata["primary_personas"][0]["pain_filters"]
    assert workspace_store.get(korea["workspace_id"]).metadata == {"guard": "must_not_be_overwritten"}

    shutil.rmtree(root)
    print("taiwan profile smoke test passed")


if __name__ == "__main__":
    main()
