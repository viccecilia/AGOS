from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.demand_to_action_strategy_engine import DemandToActionStrategyEngine


def main() -> None:
    report = DemandToActionStrategyEngine().build()
    platform_actions = report["platformContentActions"]
    business_actions = report["localBusinessActions"]
    driver_actions = report["driverOperationActions"]
    summary = report["demandActionStrategySummary"]

    assert report["status"] == "demand_action_strategy_ready"
    assert platform_actions, "must generate platform content actions"
    assert business_actions, "must generate local business actions"
    assert driver_actions, "must generate driver operation actions"
    assert summary["all_actions_need_human_review"] is True

    required_platforms = {
        "Reddit",
        "TikTok",
        "X",
        "YouTube",
        "Instagram",
        "Xiaohongshu",
        "SEO / Website",
    }
    assert required_platforms <= {item["target_platform"] for item in platform_actions}

    for action in platform_actions:
        for field in (
            "target_platform",
            "content_angle",
            "pain_point",
            "season",
            "location",
            "audience",
            "recommended_tone",
            "risk_level",
            "human_review_required",
        ):
            assert field in action, f"platform action missing {field}"
        assert action["status"] == "needs_human_review"
        assert action["human_review_required"] is True
        assert action["auto_publish_enabled"] is False
        assert action["auto_reply_enabled"] is False
        assert action["auto_dm_enabled"] is False

    required_business_types = {
        "charter_company",
        "airport_transfer_company",
        "travel_agency",
        "hotel",
        "local_dmc",
        "exhibition_service_provider",
        "event_organizer",
    }
    assert required_business_types <= {item["business_type"] for item in business_actions}
    for action in business_actions:
        for field in (
            "business_type",
            "opportunity",
            "target_location",
            "target_time_window",
            "recommended_offer",
            "required_preparation",
            "risk_notes",
        ):
            assert field in action, f"business action missing {field}"
        assert action["status"] == "needs_human_review"
        assert action["auto_contact_business_enabled"] is False
        assert action["auto_contact_customer_enabled"] is False
        assert action["auto_quote_enabled"] is False

    for action in driver_actions:
        for field in (
            "focus_standby_area",
            "priority_time_window",
            "recommended_vehicle_type",
            "language_preparation",
            "luggage_space_requirement",
            "traffic_waiting_risk",
            "service_script_suggestion",
        ):
            assert field in action, f"driver action missing {field}"
        assert action["status"] == "needs_human_review"
        assert action["auto_dispatch_enabled"] is False
        assert action["auto_contact_driver_enabled"] is False
        assert action["auto_contact_customer_enabled"] is False
        assert action["auto_quote_enabled"] is False

    assert summary["auto_publish_enabled"] is False
    assert summary["auto_contact_customer_enabled"] is False
    assert summary["auto_contact_driver_enabled"] is False
    assert summary["auto_contact_business_enabled"] is False
    assert summary["auto_dispatch_enabled"] is False
    assert summary["write_operations_enabled"] is False

    for output_name in [
        "platform_content_actions.json",
        "local_business_actions.json",
        "driver_operation_actions.json",
        "demand_action_strategy_report.json",
        "demand_action_strategy_summary.json",
    ]:
        output_path = PROJECT_ROOT / "runtime" / "demand_to_action_strategy" / output_name
        assert output_path.exists(), f"missing output: {output_name}"
        json.loads(output_path.read_text(encoding="utf-8"))

    print("demand_to_action_strategy_smoke_test passed")


if __name__ == "__main__":
    main()
