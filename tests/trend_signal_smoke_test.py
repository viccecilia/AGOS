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
    report = load_sample("eu_us_growth_report_sample.json")
    pain = load_sample("eu_us_english_pain_radar.json")
    trends = load_sample("eu_us_trend_signal_sample.json")
    pain_ids = {item["pain_point_id"] for item in pain["pain_points"]}

    assert trends["sample_data_only"] is True
    assert trends["source_report_set_id"] == report["report_set_id"]
    assert trends["recommendation_rules"]["must_label_sample_data"] is True

    suggestions = []
    for signal in trends["signals"]:
        assert signal["linked_pain_point_id"] in pain_ids
        assert signal["signal_strength"] >= trends["recommendation_rules"]["minimum_signal_strength"]
        assert signal["season"]
        assert len(signal["platform_hotspots"]) >= 2
        assert len(signal["recommended_formats"]) >= 2
        suggestions.append(
            {
                "signal_id": signal["signal_id"],
                "pain_point_id": signal["linked_pain_point_id"],
                "recommendation": signal["content_opportunity"],
                "formats": signal["recommended_formats"],
                "sample_data_only": trends["sample_data_only"],
            }
        )

    assert len(suggestions) == 3
    assert suggestions[0]["pain_point_id"] == "workflow_overload_reddit"
    assert all(item["sample_data_only"] is True for item in suggestions)

    print("trend signal smoke test passed")


if __name__ == "__main__":
    main()
