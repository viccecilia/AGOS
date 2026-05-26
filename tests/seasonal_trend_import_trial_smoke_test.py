from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.seasonal_demand_calendar_engine import SeasonalDemandCalendarEngine
from services.seasonal_trend_import_trial import SeasonalTrendImportTrial


def main() -> None:
    SeasonalDemandCalendarEngine().build()
    trial = SeasonalTrendImportTrial()
    report = trial.run()

    records = report["trendImportRecords"]
    matches = report["seasonalTrendMatches"]
    heatmap = report["seasonalMarketHeatmap"]
    interpretation = report["seasonalDemandInterpretation"]
    summary = report["seasonalTrendImportSummary"]

    assert report["status"] == "seasonal_trend_import_trial_ready"
    assert len(records) >= 8, "at least 8 sample trend records must be imported"
    assert any(record["source_type"] == "csv" for record in records), "sample CSV must be loaded"
    assert all(record["sample_data_only"] is True for record in records), "records must be sample-only"
    assert all(record["real_google_trends_api_connected"] is False for record in records)
    assert all(record["write_operations_enabled"] is False for record in records)

    matched = [item for item in matches if item["matched_season_id"] != "NO_MATCH"]
    noisy = interpretation["noisy_low_confidence_signals"]
    assert len(matched) >= 5, "at least 5 records must match seasonal calendar entries"
    assert heatmap, "market heatmap must be generated"
    assert interpretation["demand_type_ranking"], "demand type ranking must be generated"
    assert interpretation["mobility_pain_point_ranking"], "pain point ranking must be generated"
    assert interpretation["human_review_queue"], "human review queue must be generated"
    assert noisy, "low-confidence/noisy signals must be separated"
    assert all(item["confirmed_demand"] is False for item in noisy), "noisy signals cannot be confirmed demand"

    assert summary["imported_keyword_count"] == len(records)
    assert summary["matched_seasonal_signals"] == len(matched)
    assert summary["sample_data_only"] is True
    assert summary["confirmed_demand"] is False
    assert summary["api_status"] == "real_google_trends_api_not_connected"
    assert summary["write_action_status"] == "blocked"
    assert report["futureGoogleTrendsApiAdapter"]["connected"] is False
    assert "does not call Google Trends" in report["safetyBoundary"]

    for output_name in [
        "trend_import_records.json",
        "seasonal_trend_matches.json",
        "seasonal_market_heatmap.json",
        "seasonal_demand_interpretation.json",
        "seasonal_trend_import_summary.json",
    ]:
        output_path = PROJECT_ROOT / "runtime" / "seasonal_trend_import_trial" / output_name
        assert output_path.exists(), f"missing output: {output_name}"
        json.loads(output_path.read_text(encoding="utf-8"))

    print("seasonal_trend_import_trial_smoke_test passed")


if __name__ == "__main__":
    main()
