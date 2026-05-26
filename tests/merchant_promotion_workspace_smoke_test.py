from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.merchant_promotion_workspace import MerchantPromotionWorkspace


def main() -> None:
    report = MerchantPromotionWorkspace().build()
    profiles = report["merchantProfiles"]
    social = report["merchantSocialMatrix"]
    opportunities = report["homepageProblemOpportunities"]
    strategies = report["answerToHomepageStrategy"]
    review_queue = report["promotionReviewQueue"]
    summary = report["merchantPromotionSummary"]

    assert report["status"] == "merchant_promotion_workspace_ready"
    assert len(profiles) >= 2
    assert any(item["workspace_id"] == "jag_app_growth" for item in profiles)
    assert any(item["workspace_id"] == "home_appliance_demo" for item in profiles)
    assert summary["workspace_plugin_ready"] is True
    assert summary["active_workspace"] == "jag_app_growth"
    assert summary["social_homepage_slots"] >= 7
    assert summary["active_workspace_opportunities"] >= 4
    assert summary["promotion_strategies"] == len(strategies)
    assert summary["review_queue_items"] == len(review_queue)
    assert summary["all_actions_human_gated"] is True
    assert summary["auto_post_enabled"] is False
    assert summary["auto_reply_enabled"] is False
    assert summary["auto_dm_enabled"] is False
    assert summary["write_api_enabled"] is False
    assert summary["workspace_isolation_checked"] is True
    assert summary["home_appliance_demo_isolated"] is True

    for profile in profiles:
        assert profile["human_review_required"] is True
        assert profile["auto_post_enabled"] is False
        assert profile["write_api_enabled"] is False

    for item in social:
        assert item["write_permission"] is False
        assert item["auto_post_enabled"] is False
        assert item["auto_reply_enabled"] is False

    for item in opportunities:
        assert item["workspace_isolated"] is True
        assert item["sample_data_only"] is True
        assert item["needs_human_review"] is True
        assert item["allowed_to_auto_reply"] is False
        assert item["allowed_to_auto_post"] is False
        if item["workspace_id"] == "home_appliance_demo":
            assert "Japan AI Guide" not in item["merchant_name"]

    for item in strategies:
        assert item["human_review_required"] is True
        assert item["review_status"] == "needs_human_review"
        assert item["auto_post_enabled"] is False
        assert item["auto_reply_enabled"] is False
        assert item["write_api_enabled"] is False

    for output_name in [
        "merchant_profiles.json",
        "merchant_social_matrix.json",
        "homepage_problem_opportunities.json",
        "answer_to_homepage_strategy.json",
        "promotion_review_queue.json",
        "merchant_promotion_summary.json",
    ]:
        path = PROJECT_ROOT / "runtime" / "merchant_promotion_workspace" / output_name
        assert path.exists(), f"missing output: {output_name}"
        json.loads(path.read_text(encoding="utf-8"))

    print("merchant_promotion_workspace_smoke_test passed")


if __name__ == "__main__":
    main()
