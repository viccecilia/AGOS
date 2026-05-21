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
    seasonal = load_sample("seasonal_content_system.json")
    assert seasonal["sample_data_only"] is True
    assert "do not assume real-time weather" in seasonal["live_weather_or_event_policy"]
    assert set(seasonal["markets"]) == {"KR", "TW"}

    season_ids = {season["season_id"] for season in seasonal["seasons"]}
    assert {"spring_sakura", "autumn_leaves", "onsen_winter", "festival_sample"} <= season_ids

    for season in seasonal["seasons"]:
        assert season["label"]
        assert season["typical_window"]
        assert len(season["content_angles"]) >= 3
        assert set(season["market_variants"]) == {"KR", "TW"}
        if season["season_id"] == "festival_sample":
            assert "verify" in season["typical_window"].lower()

    for recommendation in seasonal["recommendation_examples"]:
        assert recommendation["market"] in {"KR", "TW"}
        assert recommendation["season_id"] in season_ids
        assert recommendation["recommendation"]

    print("seasonal content smoke test passed")


if __name__ == "__main__":
    main()
