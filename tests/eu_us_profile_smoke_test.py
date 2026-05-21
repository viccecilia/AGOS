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


def load_profile() -> dict:
    path = PROJECT_ROOT / "runtime" / "samples" / "eu_us_user_profile.json"
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    root = Path("runtime/test_eu_us_profile_workspaces")
    if root.exists():
        shutil.rmtree(root)

    profile = load_profile()
    workspace_store = WorkspaceStore(root)
    workspace_store.create(
        {
            "workspace_id": "jag_ai_guide",
            "name": "Japan AI Guide Guard Workspace",
            "owner": "AGOS",
            "product_name": "Japan AI Guide",
            "industry": "travel",
            "target_markets": ["US", "EU", "KR", "TW"],
            "status": "active",
            "metadata": {"guard": "must_not_be_overwritten"},
        }
    )
    eu_workspace = workspace_store.create(
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

    assert eu_workspace.workspace_id == "eu_us_growth_lab"
    assert "US" in eu_workspace.target_markets
    assert "DE" in eu_workspace.target_markets
    assert eu_workspace.metadata["primary_personas"][0]["persona_id"] == "solo_builder"

    pain = PainPointStore(workspace_store)
    pain.import_many(
        "eu_us_growth_lab",
        [
            {
                "pain_point_id": "workflow_overload_reddit",
                "source": "r021_local_profile_sample",
                "platform": "reddit",
                "market": "US",
                "audience": "solo_builder",
                "category": "workflow_overload",
                "title": "Founders cannot turn scattered AI tools into a weekly growth workflow",
                "evidence": "Local R021 sample maps solo_builder pain filters to Reddit discovery.",
                "trend_score": 88,
                "urgency_score": 84,
                "value_score": 91,
                "tags": ["solo_builder", "workflow_overload", "reddit"],
            },
            {
                "pain_point_id": "client_reporting_seo",
                "source": "r021_local_profile_sample",
                "platform": "seo",
                "market": "UK",
                "audience": "small_agency_operator",
                "category": "client_reporting",
                "title": "Small agencies need repeatable client growth reports without manual assembly",
                "evidence": "Local R021 sample maps agency pain filters to SEO and reporting intent.",
                "trend_score": 82,
                "urgency_score": 80,
                "value_score": 89,
                "tags": ["small_agency_operator", "client_reporting", "seo"],
            },
            {
                "pain_point_id": "message_testing_threads",
                "source": "r021_local_profile_sample",
                "platform": "threads",
                "market": "DE",
                "audience": "saas_growth_manager",
                "category": "message_testing",
                "title": "Growth managers need faster message tests before scaling content production",
                "evidence": "Local R021 sample maps SaaS growth pain filters to social testing.",
                "trend_score": 76,
                "urgency_score": 77,
                "value_score": 86,
                "tags": ["saas_growth_manager", "message_testing", "threads"],
            },
        ],
    )

    reddit_items = pain.list("eu_us_growth_lab", platform="reddit")
    assert len(reddit_items) == 1
    assert reddit_items[0].audience == "solo_builder"
    assert pain.list("eu_us_growth_lab", category="client_reporting")[0].platform == "seo"
    assert pain.top("eu_us_growth_lab", 1)[0].pain_point_id == "workflow_overload_reddit"

    jag_workspace = workspace_store.get("jag_ai_guide")
    assert jag_workspace.metadata == {"guard": "must_not_be_overwritten"}
    assert pain.list("jag_ai_guide") == []

    shutil.rmtree(root)
    print("eu/us profile smoke test passed")


if __name__ == "__main__":
    main()
