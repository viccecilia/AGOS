from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

SIMPLIFIED_MARKERS = ["视频", "交通信息", "地铁", "攻略怎么排", "点击"]


def load_sample(name: str) -> dict:
    return json.loads((PROJECT_ROOT / "runtime" / "samples" / name).read_text(encoding="utf-8"))


def main() -> None:
    profile = load_sample("taiwan_user_profile.json")
    templates = load_sample("taiwan_content_templates.json")
    persona_ids = {persona["persona_id"] for persona in profile["primary_personas"]}

    assert templates["source_profile_id"] == profile["profile_id"]
    assert templates["workspace_id"] == profile["workspace_id"]
    assert "Traditional Chinese only" in templates["language_policy"]

    generated = []
    for template in templates["templates"]:
        joined = json.dumps(template, ensure_ascii=False)
        assert template["target_persona"] in persona_ids
        assert template["content_type"] in {"deep_guide", "short_video", "social_post"}
        assert template["title"]
        assert template["hook"]
        assert template["body"]
        assert len(template["review_notes"]) >= 3
        assert not any(marker in joined for marker in SIMPLIFIED_MARKERS)
        generated.append(
            {
                "template_id": template["template_id"],
                "platform": template["platform"],
                "content_type": template["content_type"],
                "review_status": "needs_review",
            }
        )

    assert {item["content_type"] for item in generated} == {"deep_guide", "short_video", "social_post"}
    assert all(item["review_status"] == "needs_review" for item in generated)

    print("taiwan content template smoke test passed")


if __name__ == "__main__":
    main()
