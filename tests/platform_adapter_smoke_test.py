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
    adapter = load_sample("eu_us_platform_adapter_sample.json")
    pain = load_sample("eu_us_english_pain_radar.json")
    content_templates = load_sample("eu_us_english_content_templates.json")
    pain_ids = {item["pain_point_id"] for item in pain["pain_points"]}

    assert adapter["source_pain_point_id"] in pain_ids
    assert adapter["do_not_overwrite_template_set"] == content_templates["template_set_id"]

    outputs = adapter["outputs"]
    assert {item["platform"] for item in outputs} == {"reddit", "tiktok", "instagram", "youtube", "seo"}
    assert len(outputs) == 5
    for item in outputs:
        assert item["format"]
        assert item["angle"]
        assert item["headline"]
        assert item["body"]
        assert item["cta"]
        assert "automatic publish" not in json.dumps(item).lower()

    assert next(item for item in outputs if item["platform"] == "reddit")["format"] == "discussion_reply_seed"
    assert next(item for item in outputs if item["platform"] == "tiktok")["format"] == "short_video_script"
    assert next(item for item in outputs if item["platform"] == "seo")["format"] == "article_brief"

    print("platform adapter smoke test passed")


if __name__ == "__main__":
    main()
