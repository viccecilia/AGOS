from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.seasonal_demand_calendar_engine import SeasonalDemandCalendarEngine


def main() -> None:
    engine = SeasonalDemandCalendarEngine()
    report = engine.build()

    seasons = report["seasonalCalendar"]
    keywords = report["seasonalKeywords"]
    monitoring_plan = report["seasonalMonitoringPlan"]
    summary = report["seasonalDemandSummary"]

    assert len(seasons) >= 6, "seasonal calendar must include at least 6 seasons"
    assert monitoring_plan, "Google Trends monitoring plan structure must be generated"
    assert keywords, "seasonal keyword monitoring records must be generated"
    assert summary["write_operations_enabled"] is False
    assert report["safetyBoundary"]

    required_season_ids = {
        "SEASON-SAKURA",
        "SEASON-GOLDEN-WEEK",
        "SEASON-SUMMER",
        "SEASON-AUTUMN-LEAVES",
        "SEASON-CHRISTMAS",
        "SEASON-CHINESE-NEW-YEAR",
        "SEASON-JAPAN-NEW-YEAR",
        "SEASON-LONG-WEEKENDS",
        "SEASON-SCHOOL-HOLIDAYS",
        "SEASON-EVENTS",
    }
    assert required_season_ids <= {season["season_id"] for season in seasons}

    for season in seasons:
        assert season["season_id"]
        assert season["season_name"]
        assert season["time_window"], f"{season['season_id']} missing time_window"
        assert season["target_markets"], f"{season['season_id']} missing target_markets"
        assert season["likely_locations"], f"{season['season_id']} missing likely_locations"
        assert season["demand_keywords"], f"{season['season_id']} missing demand_keywords"
        assert season["mobility_pain_points"], f"{season['season_id']} missing mobility_pain_points"
        assert season["predicted_demand_types"], f"{season['season_id']} missing predicted_demand_types"
        assert season["monitoring_frequency"], f"{season['season_id']} missing monitoring_frequency"
        assert season["risk_notes"], f"{season['season_id']} missing risk_notes"
        assert season["real_api_connected"] is False
        assert season["write_operations_enabled"] is False

    expected_keyword_examples = {
        "Japan cherry blossom travel",
        "Tokyo airport transfer",
        "Japan Golden Week travel",
        "Kyoto autumn leaves",
        "Japan summer family trip",
        "Japan Chinese New Year travel",
        "Osaka airport pickup",
        "Tokyo luggage transfer",
    }
    keyword_text = " ".join(item["keyword"] for item in keywords)
    for expected in expected_keyword_examples:
        assert expected in keyword_text, f"missing keyword example: {expected}"

    for output_name in [
        "seasonal_calendar.json",
        "seasonal_keywords.json",
        "seasonal_monitoring_plan.json",
        "seasonal_demand_summary.json",
    ]:
        output_path = PROJECT_ROOT / "runtime" / "seasonal_demand_calendar" / output_name
        assert output_path.exists(), f"missing output: {output_name}"
        json.loads(output_path.read_text(encoding="utf-8"))

    print("seasonal_demand_calendar_smoke_test passed")


if __name__ == "__main__":
    main()
