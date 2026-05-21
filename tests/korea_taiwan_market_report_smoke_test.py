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
    korea_profile = load_sample("korea_user_profile.json")
    taiwan_profile = load_sample("taiwan_user_profile.json")
    pain = load_sample("korea_taiwan_pain_points.json")
    replies = load_sample("korea_taiwan_reply_workflow_rules.json")
    seasonal = load_sample("seasonal_content_system.json")
    report = load_sample("korea_taiwan_market_report_sample.json")

    assert report["sample_data_only"] is True
    for artifact in [
        korea_profile["profile_id"],
        taiwan_profile["profile_id"],
        pain["pain_library_id"],
        replies["rule_set_id"],
        seasonal["seasonal_system_id"],
    ]:
        assert artifact in report["source_artifacts"]

    reports = {item["market"]: item for item in report["reports"]}
    assert set(reports) == {"KR", "TW"}
    assert reports["KR"]["language"] == "ko"
    assert reports["TW"]["language"] == "zh-Hant"
    assert reports["KR"]["metrics"]["pain_points"] == 2
    assert reports["TW"]["metrics"]["pain_points"] == 2
    assert reports["TW"]["metrics"]["language_guard"] == "Traditional Chinese only"

    for item in report["reports"]:
        assert item["summary"].startswith("Sample")
        assert len(item["recommendations"]) >= 3

    print("korea/taiwan market report smoke test passed")


if __name__ == "__main__":
    main()
