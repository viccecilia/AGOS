from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.opportunity_qualification_engine import OpportunityQualificationEngine
from services.problem_seeker_loop import ProblemSeekerLoop


def main() -> None:
    ProblemSeekerLoop().run()
    report = OpportunityQualificationEngine().qualify()
    opportunities = report["qualifiedOpportunities"]
    ranking = report["opportunityRanking"]
    risk_review = report["opportunityRiskReview"]
    summary = report["opportunityQualificationSummary"]

    assert report["status"] == "opportunity_qualification_ready"
    assert len(opportunities) >= 5
    assert len(ranking) == len(opportunities)
    assert summary["opportunity_qualification_ready"] is True
    assert summary["high_value_count"] >= 1
    assert summary["monitor_count"] >= 1 or summary["low_value_count"] >= 1
    assert summary["human_review_required"] is True
    assert summary["auto_action_allowed"] is False
    assert risk_review["all_actions_human_gated"] is True
    assert risk_review["auto_action_allowed_for_unsafe"] is False

    required = {
        "opportunity_id",
        "problem_id",
        "workspace_id",
        "merchant_name",
        "platform",
        "market",
        "question_text",
        "score_breakdown",
        "total_score",
        "qualification_status",
        "qualification_reason",
        "recommended_next_step",
        "human_review_required",
        "auto_action_allowed",
    }
    score_fields = {
        "pain_strength",
        "homepage_fit",
        "answerability",
        "platform_suitability",
        "conversion_potential",
        "risk_level",
        "spam_risk",
        "brand_fit",
    }
    statuses = {item["qualification_status"] for item in opportunities}
    assert statuses <= {"high_value", "monitor", "low_value", "unsafe"}
    for item in opportunities:
        assert required <= set(item), f"missing opportunity fields: {item}"
        assert score_fields <= set(item["score_breakdown"]), f"missing score fields: {item}"
        assert item["workspace_id"] == "jag_app_growth"
        assert item["human_review_required"] is True
        assert item["auto_action_allowed"] is False
        if item["qualification_status"] == "unsafe":
            assert item["recommended_next_step"] == "block_auto_action_and_request_manual_correction"
            assert item["auto_action_allowed"] is False

    for output_name in [
        "qualified_opportunities.json",
        "opportunity_ranking.json",
        "opportunity_risk_review.json",
        "opportunity_qualification_summary.json",
    ]:
        path = PROJECT_ROOT / "runtime" / "opportunity_qualification" / output_name
        assert path.exists(), f"missing output: {output_name}"
        json.loads(path.read_text(encoding="utf-8"))

    print("opportunity_qualification_smoke_test passed")


if __name__ == "__main__":
    main()
