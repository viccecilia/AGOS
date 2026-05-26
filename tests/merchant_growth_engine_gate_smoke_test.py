from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.merchant_growth_engine_gate import MerchantGrowthEngineGate


def main() -> None:
    gate = MerchantGrowthEngineGate().evaluate()
    report = gate["merchantGrowthEngineReport"]
    safety = gate["merchantGrowthEngineSafetyReview"]
    checks = gate["merchantGrowthEngineChecks"]
    summary = gate["merchantGrowthEngineSummary"]

    assert gate["status"] == "merchant_growth_engine_gate_passed"
    assert len(checks) == 7
    assert all(item["status"] == "passed" for item in checks), "all seven core modules must pass"

    assert report["workspace_plugin_ready"] is True
    assert report["problem_seeker_ready"] is True
    assert report["opportunity_qualification_ready"] is True
    assert report["answer_draft_ready"] is True
    assert report["cross_platform_plan_ready"] is True
    assert report["review_center_ready"] is True
    assert report["feedback_learning_ready"] is True
    assert report["safety_boundary_passed"] is True
    assert report["next_stage_recommendation"]
    assert report["candidate_problem_count"] >= 5
    assert report["high_value_opportunity_count"] >= 1
    assert report["answer_draft_count"] >= 3
    assert report["cross_platform_plan_count"] >= 5
    assert report["review_item_count"] >= 1
    assert report["feedback_event_count"] >= 5

    assert safety["workspace_isolation"] is True
    assert safety["human_review_gate"] is True
    assert safety["safety_boundary_passed"] is True
    assert safety["home_appliance_pollution_detected"] is False
    assert safety["auto_spam_enabled"] is False
    assert safety["auto_post_enabled"] is False
    assert safety["auto_reply_enabled"] is False
    assert safety["auto_dm_enabled"] is False
    assert safety["write_api_enabled"] is False
    assert safety["login_scraping_enabled"] is False
    assert all(safety["blocked_flags"].values())

    assert summary["merchant_growth_engine_ready"] is True
    assert summary["gate_passed"] is True
    assert summary["phase_completed"] is True
    assert summary["workspace_plugin_ready"] is True
    assert summary["problem_seeker_ready"] is True
    assert summary["opportunity_qualification_ready"] is True
    assert summary["answer_draft_ready"] is True
    assert summary["cross_platform_plan_ready"] is True
    assert summary["review_center_ready"] is True
    assert summary["feedback_learning_ready"] is True
    assert summary["safety_boundary_passed"] is True
    assert summary["auto_post_enabled"] is False
    assert summary["auto_reply_enabled"] is False
    assert summary["auto_dm_enabled"] is False
    assert summary["write_api_enabled"] is False
    assert summary["login_scraping_enabled"] is False
    assert summary["next_stage_recommendation"]

    for output_name in [
        "MERCHANT_GROWTH_ENGINE_REPORT.json",
        "MERCHANT_GROWTH_ENGINE_SAFETY_REVIEW.json",
        "merchant_growth_engine_checks.json",
        "merchant_growth_engine_summary.json",
    ]:
        path = PROJECT_ROOT / "runtime" / "merchant_growth_engine_gate" / output_name
        assert path.exists(), f"missing output: {output_name}"
        json.loads(path.read_text(encoding="utf-8"))

    print("merchant_growth_engine_gate_smoke_test passed")


if __name__ == "__main__":
    main()
