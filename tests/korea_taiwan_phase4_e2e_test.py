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
    expected_reports = [f"R{index:03d}" for index in range(31, 41)]
    existing_reports = {
        path.parent.name
        for path in (PROJECT_ROOT / "runtime" / "task_results").glob("R*/ROUND_SUMMARY.md")
    }
    missing = [round_id for round_id in expected_reports[:-1] if round_id not in existing_reports]
    assert not missing, f"Missing reports: {missing}"

    korea_profile = load_sample("korea_user_profile.json")
    korea_templates = load_sample("korea_content_templates.json")
    korea_visual = load_sample("korea_visual_content_strategy.json")
    taiwan_profile = load_sample("taiwan_user_profile.json")
    taiwan_templates = load_sample("taiwan_content_templates.json")
    pain = load_sample("korea_taiwan_pain_points.json")
    replies = load_sample("korea_taiwan_reply_workflow_rules.json")
    seasonal = load_sample("seasonal_content_system.json")
    report = load_sample("korea_taiwan_market_report_sample.json")

    assert korea_templates["source_profile_id"] == korea_profile["profile_id"]
    assert korea_visual["source_template_set_id"] == korea_templates["template_set_id"]
    assert taiwan_templates["source_profile_id"] == taiwan_profile["profile_id"]
    assert set(pain["workspaces"]) == {korea_profile["workspace_id"], taiwan_profile["workspace_id"]}
    assert replies["source_pain_library_id"] == pain["pain_library_id"]
    assert seasonal["sample_data_only"] is True
    assert report["sample_data_only"] is True
    assert pain["pain_library_id"] in report["source_artifacts"]
    assert replies["rule_set_id"] in report["source_artifacts"]
    assert seasonal["seasonal_system_id"] in report["source_artifacts"]

    markets = {item["market"] for item in report["reports"]}
    languages = {item["language"] for item in report["reports"]}
    assert markets == {"KR", "TW"}
    assert languages == {"ko", "zh-Hant"}

    print("korea/taiwan phase4 e2e test passed")


if __name__ == "__main__":
    main()
