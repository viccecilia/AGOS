from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.workspace_service import WorkspaceStore


def load_profile() -> dict:
    return json.loads((PROJECT_ROOT / "runtime" / "samples" / "korea_user_profile.json").read_text(encoding="utf-8"))


def main() -> None:
    profile = load_profile()
    assert profile["workspace_id"] == "korea_growth_lab"
    assert profile["localization_rules"]["language"] == "ko"
    assert "literal machine translation" in profile["localization_rules"]["avoid"]

    root = Path("runtime/test_korea_profile_workspaces")
    if root.exists():
        shutil.rmtree(root)

    workspace_store = WorkspaceStore(root)
    workspace_store.create(
        {
            "workspace_id": "eu_us_growth_lab",
            "name": "Europe and US Guard Workspace",
            "owner": "AGOS",
            "product_name": "AI Growth Operating System",
            "industry": "growth_software",
            "target_markets": ["US", "UK", "DE", "FR"],
            "status": "active",
            "metadata": {"guard": "must_not_be_overwritten"},
        }
    )
    korea = workspace_store.create(
        {
            "workspace_id": profile["workspace_id"],
            "name": "Korea Growth Lab",
            "owner": "AGOS",
            "product_name": "AI Growth Operating System",
            "industry": "travel_growth",
            "target_markets": profile["markets"],
            "status": "active",
            "metadata": {
                "profile_id": profile["profile_id"],
                "primary_personas": profile["primary_personas"],
                "localization_rules": profile["localization_rules"],
            },
        }
    )

    assert korea.target_markets == ["KR"]
    assert korea.metadata["primary_personas"][0]["persona_id"] == "first_time_japan_planner"
    assert "instagram" in korea.metadata["primary_personas"][0]["platform_preferences"]
    assert "route_confusion" in korea.metadata["primary_personas"][0]["pain_filters"]
    assert workspace_store.get("eu_us_growth_lab").metadata == {"guard": "must_not_be_overwritten"}

    shutil.rmtree(root)
    print("korea profile smoke test passed")


if __name__ == "__main__":
    main()
