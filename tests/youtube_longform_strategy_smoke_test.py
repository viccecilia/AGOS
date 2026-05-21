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
    content_templates = load_sample("eu_us_english_content_templates.json")
    youtube = load_sample("eu_us_youtube_longform_strategy.json")
    assert youtube["source_content_template_set_id"] == content_templates["template_set_id"]
    assert "avoid misleading claims" in youtube["accuracy_policy"]

    episodes = youtube["episodes"]
    assert len(episodes) == 1
    episode = episodes[0]
    assert episode["title"]
    assert episode["target_viewer"]
    assert episode["promise"]
    assert len(episode["chapters"]) >= 5
    assert all(chapter["chapter"] and len(chapter["beats"]) >= 2 for chapter in episode["chapters"])
    assert len(episode["script_outline"]) >= 4

    seo = episode["seo"]
    assert seo["primary_keyword"] == "AI growth workflow"
    assert len(seo["secondary_keywords"]) >= 3
    assert len(seo["description"]) >= 80
    assert seo["thumbnail_text"]
    claim_text = " ".join(
        [episode["title"], episode["promise"], *episode["script_outline"]]
    ).lower()
    assert "guaranteed growth" not in claim_text
    assert "not a guaranteed growth claim" in seo["disclaimer"]

    print("youtube longform strategy smoke test passed")


if __name__ == "__main__":
    main()
