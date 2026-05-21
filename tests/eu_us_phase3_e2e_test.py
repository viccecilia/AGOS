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
    expected_reports = [f"R{index:03d}" for index in range(21, 31)]
    existing_reports = {
        path.parent.name
        for path in (PROJECT_ROOT / "runtime" / "task_results").glob("R*/ROUND_SUMMARY.md")
    }
    missing = [round_id for round_id in expected_reports[:-1] if round_id not in existing_reports]
    assert not missing, f"Missing reports: {missing}"

    profile = load_sample("eu_us_user_profile.json")
    pain = load_sample("eu_us_english_pain_radar.json")
    content = load_sample("eu_us_english_content_templates.json")
    replies = load_sample("eu_us_reply_workflow_rules.json")
    short_video = load_sample("eu_us_short_video_packages.json")
    youtube = load_sample("eu_us_youtube_longform_strategy.json")
    report = load_sample("eu_us_growth_report_sample.json")
    trends = load_sample("eu_us_trend_signal_sample.json")
    adapter = load_sample("eu_us_platform_adapter_sample.json")

    assert profile["workspace_id"] == "eu_us_growth_lab"
    assert pain["source_profile_id"] == profile["profile_id"]
    assert content["source_radar_id"] == pain["radar_id"]
    assert replies["workspace_id"] == profile["workspace_id"]
    assert short_video["source_template_set_id"] == content["template_set_id"]
    assert youtube["source_content_template_set_id"] == content["template_set_id"]
    assert report["sample_data_only"] is True
    assert trends["source_report_set_id"] == report["report_set_id"]
    assert adapter["source_pain_point_id"] in {item["pain_point_id"] for item in pain["pain_points"]}

    assert {item["platform"] for item in adapter["outputs"]} == {
        "reddit",
        "tiktok",
        "instagram",
        "youtube",
        "seo",
    }
    assert all("sample" in item["summary"].lower() for item in report["reports"])
    assert trends["sample_data_only"] is True

    print("eu/us phase3 e2e test passed")


if __name__ == "__main__":
    main()
