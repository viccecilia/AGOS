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
    pain = load_sample("eu_us_english_pain_radar.json")
    content = load_sample("eu_us_english_content_templates.json")
    replies = load_sample("eu_us_reply_workflow_rules.json")
    short_video = load_sample("eu_us_short_video_packages.json")
    youtube = load_sample("eu_us_youtube_longform_strategy.json")
    report = load_sample("eu_us_growth_report_sample.json")

    assert report["sample_data_only"] is True
    assert pain["radar_id"] in report["source_artifacts"]
    assert content["template_set_id"] in report["source_artifacts"]
    assert replies["rule_set_id"] in report["source_artifacts"]
    assert short_video["package_set_id"] in report["source_artifacts"]
    assert youtube["strategy_id"] in report["source_artifacts"]

    reports = {item["report_type"]: item for item in report["reports"]}
    assert set(reports) == {"daily", "weekly", "optimization"}
    assert reports["daily"]["metrics"]["pain_points"] == len(pain["pain_points"])
    assert reports["daily"]["metrics"]["content_templates"] == len(content["templates"])
    assert reports["daily"]["metrics"]["reply_samples"] == len(replies["sample_questions"])
    assert reports["daily"]["metrics"]["short_video_packages"] == len(short_video["packages"])
    assert reports["daily"]["metrics"]["youtube_strategies"] == len(youtube["episodes"])
    assert reports["weekly"]["metrics"]["stage_gate"] == "pending R030"
    assert reports["optimization"]["metrics"]["recommended_next_round"] == "R028"

    for item in report["reports"]:
        assert item["title"]
        assert item["summary"].startswith("Sample")
        assert len(item["recommendations"]) >= 3
        assert "live market performance" not in item["summary"].lower()

    print("english growth report smoke test passed")


if __name__ == "__main__":
    main()
