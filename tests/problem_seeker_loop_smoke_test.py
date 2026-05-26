from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.merchant_promotion_workspace import MerchantPromotionWorkspace
from services.problem_seeker_loop import ProblemSeekerLoop


def main() -> None:
    MerchantPromotionWorkspace().build()
    report = ProblemSeekerLoop().run()
    candidates = report["problemCandidates"]
    feed = report["problemSeekerFeed"]
    source_summary = report["problemSourceSummary"]
    summary = report["problemSeekerSummary"]
    profile = report["activeMerchantProfile"]

    assert report["status"] == "problem_seeker_loop_ready"
    assert profile["workspace_id"] == "jag_app_growth"
    assert profile["merchant_name"] == "Japan AI Guide App"
    assert len(candidates) >= 5, "at least 5 candidates expected"
    assert len(feed) == len(candidates)
    assert source_summary["source_type_counts"]
    assert summary["problem_seeker_ready"] is True
    assert summary["active_workspace"] == "jag_app_growth"
    assert summary["candidate_count"] == len(candidates)
    assert summary["all_candidates_need_human_review"] is True
    assert summary["auto_reply_allowed"] is False
    assert summary["auto_post_allowed"] is False
    assert summary["write_api_called"] is False
    assert summary["real_platform_api_called"] is False
    assert summary["sample_data_only"] is True
    assert summary["workspace_isolation_checked"] is True
    assert summary["home_appliance_pollution_detected"] is False

    required_fields = {
        "problem_id",
        "workspace_id",
        "merchant_name",
        "source_type",
        "source_platform",
        "market",
        "language",
        "question_text",
        "pain_points",
        "detected_intent",
        "homepage_fit_reason",
        "candidate_score",
        "review_status",
        "sample_data_only",
        "auto_reply_allowed",
    }
    for item in candidates:
        assert required_fields <= set(item), f"missing fields: {item}"
        assert item["workspace_id"] == "jag_app_growth"
        assert item["merchant_name"] == "Japan AI Guide App"
        assert item["review_status"] == "needs_human_review"
        assert item["sample_data_only"] is True
        assert item["auto_reply_allowed"] is False
        assert item["auto_post_allowed"] is False
        assert item["write_api_called"] is False
        assert "air fryer" not in item["question_text"].lower(), "Home Appliance question polluted JAG workspace"

    for output_name in [
        "problem_candidates.json",
        "problem_seeker_feed.json",
        "problem_source_summary.json",
        "problem_seeker_summary.json",
    ]:
        path = PROJECT_ROOT / "runtime" / "problem_seeker_loop" / output_name
        assert path.exists(), f"missing output: {output_name}"
        json.loads(path.read_text(encoding="utf-8"))

    print("problem_seeker_loop_smoke_test passed")


if __name__ == "__main__":
    main()
