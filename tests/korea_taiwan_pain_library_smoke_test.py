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
    pain_library = load_sample("korea_taiwan_pain_points.json")

    assert pain_library["sample_data_only"] is True
    assert set(pain_library["workspaces"]) == {
        korea_profile["workspace_id"],
        taiwan_profile["workspace_id"],
    }

    by_market = {"KR": [], "TW": []}
    by_language = {"ko": [], "zh-Hant": []}
    for pain in pain_library["pain_points"]:
        by_market[pain["market"]].append(pain)
        by_language[pain["language"]].append(pain)
        assert pain["workspace_id"] in pain_library["workspaces"]
        assert 0 <= pain["trend_score"] <= 100
        assert 0 <= pain["urgency_score"] <= 100
        assert 0 <= pain["value_score"] <= 100
        assert pain["tags"]

    assert len(by_market["KR"]) == 2
    assert len(by_market["TW"]) == 2
    assert {item["language"] for item in by_market["KR"]} == {"ko"}
    assert {item["language"] for item in by_market["TW"]} == {"zh-Hant"}
    assert len(by_language["ko"]) == 2
    assert len(by_language["zh-Hant"]) == 2

    top_kr = max(by_market["KR"], key=lambda item: item["trend_score"] * 0.45 + item["urgency_score"] * 0.30 + item["value_score"] * 0.25)
    top_tw = max(by_market["TW"], key=lambda item: item["trend_score"] * 0.45 + item["urgency_score"] * 0.30 + item["value_score"] * 0.25)
    assert top_kr["pain_point_id"] == "kr_route_confusion_station"
    assert top_tw["pain_point_id"] == "tw_family_route_planning"

    print("korea/taiwan pain library smoke test passed")


if __name__ == "__main__":
    main()
