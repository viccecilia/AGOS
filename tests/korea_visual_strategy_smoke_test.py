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
    templates = load_sample("korea_content_templates.json")
    visual = load_sample("korea_visual_content_strategy.json")
    template_ids = {item["template_id"] for item in templates["templates"]}
    rule_ids = {item["rule_id"] for item in visual["visual_rules"]}

    assert visual["source_template_set_id"] == templates["template_set_id"]
    assert visual["asset_policy"] == "strategy only; no real image assets generated"
    assert len(visual["visual_rules"]) >= 3

    for rule in visual["visual_rules"]:
        assert rule["target_persona"]
        assert rule["content_style"]
        assert len(rule["shot_preferences"]) >= 3
        assert len(rule["layout_preferences"]) >= 3
        assert len(rule["avoid"]) >= 3
        assert "fake live trend label" not in rule["content_style"].lower()

    for example in visual["recommendation_examples"]:
        assert example["template_id"] in template_ids
        assert example["visual_rule_id"] in rule_ids
        assert example["recommendation"]

    print("korea visual strategy smoke test passed")


if __name__ == "__main__":
    main()
