from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.predictive_demand_gate import PredictiveDemandGate


def main() -> None:
    gate = PredictiveDemandGate().evaluate()
    report = gate["predictiveDemandReport"]
    safety = gate["demandIntelligenceSafetyReview"]
    checks = gate["predictiveDemandChecks"]
    summary = gate["predictiveDemandSummary"]

    assert gate["status"] == "predictive_demand_gate_passed"
    assert len(checks) == 4
    assert all(item["status"] == "passed" for item in checks), "all four core modules must pass"
    assert report["time_trend_readiness"] is True
    assert report["location_trend_readiness"] is True
    assert report["demand_intent_readiness"] is True
    assert report["action_strategy_readiness"] is True
    assert report["high_value_seasons"]
    assert report["high_value_locations"]
    assert report["high_value_mobility_intents"]
    assert report["recommended_actions"]["platform_content_actions"]
    assert report["recommended_actions"]["local_business_actions"]
    assert report["recommended_actions"]["driver_operation_actions"]
    assert report["next_phase_recommendation"]

    assert safety["sample_data_used"] is True
    assert safety["prediction_not_real_outcome"] is True
    assert safety["low_value_filter_active"] is True
    assert safety["all_actions_human_gated"] is True
    assert safety["automatic_external_execution_enabled"] is False
    assert safety["requires_human_review"] is True
    for flag_name, flag_value in safety["automated_external_action_flags"].items():
        assert flag_value is False, f"{flag_name} must stay disabled"

    assert summary["gate_passed"] is True
    assert summary["phase_completed"] is True
    assert summary["next_phase_recommendation"]
    assert summary["all_external_actions_human_gated"] is True
    assert summary["automatic_external_execution_enabled"] is False
    assert summary["write_operations_enabled"] is False

    for output_name in [
        "PREDICTIVE_DEMAND_REPORT.json",
        "DEMAND_INTELLIGENCE_SAFETY_REVIEW.json",
        "predictive_demand_checks.json",
        "predictive_demand_summary.json",
    ]:
        output_path = PROJECT_ROOT / "runtime" / "predictive_demand_gate" / output_name
        assert output_path.exists(), f"missing output: {output_name}"
        json.loads(output_path.read_text(encoding="utf-8"))

    print("predictive_demand_gate_smoke_test passed")


if __name__ == "__main__":
    main()
