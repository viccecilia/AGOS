from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.content_engine import ContentDraftStore
from services.pain_point_engine import PainPointStore
from services.workspace_service import WorkspaceStore


def load_sample(name: str) -> dict:
    return json.loads((PROJECT_ROOT / "runtime" / "samples" / name).read_text(encoding="utf-8"))


def render(pattern: str, pain: dict) -> str:
    return pattern.format(
        audience=pain["audience"],
        category=pain["category"].replace("_", " "),
        evidence=pain["evidence"],
        title=pain["title"],
    )


def main() -> None:
    profile = load_sample("eu_us_user_profile.json")
    radar = load_sample("eu_us_english_pain_radar.json")
    templates = load_sample("eu_us_english_content_templates.json")
    assert templates["source_radar_id"] == radar["radar_id"]

    root = Path("runtime/test_english_content_factory_workspaces")
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
            "metadata": {"profile_id": profile["profile_id"]},
        }
    )

    pain_store = PainPointStore(workspace_store)
    pain_store.import_many(profile["workspace_id"], radar["pain_points"])
    top_pain = pain_store.top(profile["workspace_id"], 4)
    assert len(top_pain) == 4

    content_store = ContentDraftStore(workspace_store, pain_point_store=pain_store)
    created = []
    for index, pain_point in enumerate(top_pain):
        pain_payload = next(
            item for item in radar["pain_points"]
            if item["pain_point_id"] == pain_point.pain_point_id
        )
        template = templates["templates"][index % len(templates["templates"])]
        created.append(
            content_store.upsert(
                {
                    "draft_id": f"{pain_point.pain_point_id}_{template['content_type']}",
                    "workspace_id": profile["workspace_id"],
                    "pain_point_id": pain_point.pain_point_id,
                    "platform": template["platform"],
                    "format": template["format"],
                    "title": render(template["hook_pattern"], pain_payload),
                    "hook": render(template["hook_pattern"], pain_payload),
                    "body": render(template["body_pattern"], pain_payload),
                    "tags": pain_point.tags + template["required_tags"],
                    "review_status": "needs_review",
                    "metadata": {
                        "template_id": template["template_id"],
                        "content_type": template["content_type"],
                        "source_radar_id": radar["radar_id"],
                    },
                }
            )
        )

    assert {draft.metadata["content_type"] for draft in created} == {
        "image_text",
        "short_video",
        "long_form",
        "seo",
    }
    assert {draft.format for draft in created} == {
        "post",
        "short_video",
        "youtube_outline",
        "seo_article",
    }
    assert all(draft.review_status == "needs_review" for draft in created)
    assert len({draft.pain_point_id for draft in created}) == 4
    assert len(content_store.list(profile["workspace_id"], platform="seo")) == 1

    shutil.rmtree(root)
    print("english content factory smoke test passed")


if __name__ == "__main__":
    main()
