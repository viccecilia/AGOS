from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.pain_point_engine import PainPointStore
from services.workspace_service import WorkspaceStore


def load_sample(name: str) -> dict:
    path = PROJECT_ROOT / "runtime" / "samples" / name
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    profile = load_sample("eu_us_user_profile.json")
    radar = load_sample("eu_us_english_pain_radar.json")
    assert radar["source_profile_id"] == profile["profile_id"]

    root = Path("runtime/test_english_pain_radar_workspaces")
    if root.exists():
        shutil.rmtree(root)

    workspace_store = WorkspaceStore(root)
    workspace_store.create(
        {
            "workspace_id": profile["workspace_id"],
            "name": "Europe and US Growth Lab",
            "owner": "AGOS",
            "product_name": "AI Growth Operating System",
            "industry": "growth_software",
            "target_markets": profile["markets"],
            "status": "active",
            "metadata": {
                "profile_id": profile["profile_id"],
                "primary_personas": profile["primary_personas"],
                "selection_rules": profile["selection_rules"],
            },
        }
    )

    allowed_filters = {
        persona["persona_id"]: set(persona["pain_filters"])
        for persona in profile["primary_personas"]
    }
    for item in radar["pain_points"]:
        assert item["category"] in allowed_filters[item["audience"]]
        assert item["market"] in profile["markets"]

    pain = PainPointStore(workspace_store)
    pain.import_many(profile["workspace_id"], radar["pain_points"])

    reddit_items = pain.list(profile["workspace_id"], platform="reddit")
    assert [item.pain_point_id for item in reddit_items] == ["workflow_overload_reddit"]

    seo_items = pain.list(profile["workspace_id"], platform="seo")
    assert {item.pain_point_id for item in seo_items} == {
        "client_reporting_seo",
        "seo_prioritization_quora_style",
    }
    assert any(item.metadata["question_style"] == "quora_style_question" for item in seo_items)

    top_ids = [item.pain_point_id for item in pain.top(profile["workspace_id"], 2)]
    assert top_ids == ["workflow_overload_reddit", "client_reporting_seo"]

    shutil.rmtree(root)
    print("english pain radar smoke test passed")


if __name__ == "__main__":
    main()
