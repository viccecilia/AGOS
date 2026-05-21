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
    short_video = load_sample("eu_us_short_video_packages.json")
    assert short_video["source_template_set_id"] == content_templates["template_set_id"]
    assert short_video["publishing_policy"] == "no automatic upload"

    packages = short_video["packages"]
    assert {item["platform"] for item in packages} == {"tiktok", "instagram"}
    required_fields = {
        "package_id",
        "platform",
        "pain_point_id",
        "hook",
        "script",
        "shot_suggestions",
        "caption",
        "hashtags",
    }
    for package in packages:
        assert required_fields <= set(package)
        assert package["platform"] in short_video["platform_rules"]
        assert len(package["hook"]) >= 20
        assert len(package["script"]) >= 4
        assert len(package["shot_suggestions"]) >= 3
        assert len(package["hashtags"]) >= 4
        assert all(isinstance(line, str) and line.strip() for line in package["script"])
        assert "upload" not in " ".join(package["script"]).lower()

    print("short video package smoke test passed")


if __name__ == "__main__":
    main()
