from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.location_demand_heatmap_engine import LocationDemandHeatmapEngine
from services.seasonal_demand_calendar_engine import SeasonalDemandCalendarEngine


def main() -> None:
    seasonal = SeasonalDemandCalendarEngine().build()
    report = LocationDemandHeatmapEngine().build(seasonal["seasonalCalendar"])

    assert report["status"] == "location_heatmap_ready"
    assert report["safetyBoundary"]

    heatmap = report["locationHeatmap"]
    signals = report["locationDemandSignals"]
    risks = report["locationMobilityRisk"]
    summary = report["locationHeatmapSummary"]

    assert len(heatmap) >= 10, "heatmap must include at least 10 locations"
    assert signals, "location demand signals must be generated"
    assert risks, "location mobility risks must be generated"
    assert summary["seasonal_calendar_linked"] is True
    assert summary["real_time_crowd_data_connected"] is False
    assert summary["gps_dispatch_enabled"] is False
    assert summary["write_operations_enabled"] is False

    required_locations = {
        "Tokyo",
        "Haneda Airport",
        "Narita Airport",
        "Shinjuku",
        "Shibuya",
        "Ueno",
        "Osaka",
        "Kansai Airport",
        "Kyoto",
        "Nagoya",
        "Chubu Centrair Airport",
        "Suzuka Circuit",
        "Mount Fuji",
        "Sapporo",
        "Okinawa",
    }
    by_name = {item["location_name"]: item for item in heatmap}
    assert required_locations <= set(by_name), f"missing required locations: {required_locations - set(by_name)}"

    required_fields = {
        "location_id",
        "location_name",
        "location_type",
        "region",
        "related_seasons",
        "related_events",
        "mobility_demand_types",
        "common_pain_points",
        "crowd_risk_score",
        "transfer_complexity_score",
        "luggage_difficulty_score",
        "demand_heat_score",
    }
    for location in heatmap:
        assert required_fields <= set(location), f"{location.get('location_name')} missing fields"
        assert location["location_type"], f"{location['location_name']} missing location_type"
        assert 0 <= location["demand_heat_score"] <= 100
        assert location["mobility_demand_types"], f"{location['location_name']} missing mobility demand"
        assert location["common_pain_points"], f"{location['location_name']} missing pain points"
        assert location["real_time_crowd_data_connected"] is False
        assert location["gps_dispatch_enabled"] is False
        assert location["write_operations_enabled"] is False

    location_types = {item["location_type"] for item in heatmap}
    assert "city" in location_types
    assert "airport" in location_types
    assert "attraction" in location_types
    assert {"racing_venue", "exhibition_center"} & location_types

    assert "Sakura Season" in by_name["Tokyo"]["related_seasons"]
    assert "Sakura Season" in by_name["Ueno"]["related_seasons"]
    assert "Sakura Season" in by_name["Kyoto"]["related_seasons"]
    assert "Autumn Leaves Season" in by_name["Kyoto"]["related_seasons"]
    assert "Autumn Leaves Season" in by_name["Mount Fuji"]["related_seasons"]
    assert "Chinese New Year Travel" in by_name["Tokyo"]["related_seasons"]
    assert "Chinese New Year Travel" in by_name["Osaka"]["related_seasons"]
    assert "Chinese New Year Travel" in by_name["Haneda Airport"]["related_seasons"]
    assert "Exhibitions Concerts Sports Events" in by_name["Suzuka Circuit"]["related_seasons"]
    assert "Exhibitions Concerts Sports Events" in by_name["Nagoya"]["related_seasons"]
    assert "Exhibitions Concerts Sports Events" in by_name["Chubu Centrair Airport"]["related_seasons"]

    for output_name in [
        "location_heatmap.json",
        "location_demand_signals.json",
        "location_mobility_risk.json",
        "location_heatmap_summary.json",
    ]:
        output_path = PROJECT_ROOT / "runtime" / "location_demand_heatmap" / output_name
        assert output_path.exists(), f"missing output: {output_name}"
        json.loads(output_path.read_text(encoding="utf-8"))

    print("location_demand_heatmap_smoke_test passed")


if __name__ == "__main__":
    main()
