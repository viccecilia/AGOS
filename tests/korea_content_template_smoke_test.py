from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def load_sample(name: str) -> dict:
    return json.loads((PROJECT_ROOT / "runtime" / "samples" / name).read_text(encoding="utf-8"))


def main() -> None:
    profile = load_sample("korea_user_profile.json")
    templates = load_sample("korea_content_templates.json")
    persona_ids = {persona["persona_id"] for persona in profile["primary_personas"]}

    assert templates["source_profile_id"] == profile["profile_id"]
    assert templates["workspace_id"] == profile["workspace_id"]
    assert "no literal machine translation" in templates["localization_policy"]

    generated = []
    for template in templates["templates"]:
        assert template["target_persona"] in persona_ids
        assert template["platform"] in {"tiktok", "instagram", "youtube", "seo"}
        assert template["format"] in {"short_video", "post", "youtube_outline", "seo_article"}
        assert template["hook"]
        assert template["body"]
        assert len(template["review_notes"]) >= 3
        assert "literal translation" not in template["body"].lower()
        generated.append(
            {
                "title": template["hook"],
                "platform": template["platform"],
                "format": template["format"],
                "review_status": "needs_review",
            }
        )

    assert len(generated) == 4
    assert {item["platform"] for item in generated} == {"tiktok", "instagram", "youtube", "seo"}
    assert all(item["review_status"] == "needs_review" for item in generated)

    print("korea content template smoke test passed")


if __name__ == "__main__":
    main()
