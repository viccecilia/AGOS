from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.answer_to_homepage_draft_engine import AnswerToHomepageDraftEngine
from services.cross_platform_promotion_plan_engine import CrossPlatformPromotionPlanEngine


def main() -> None:
    AnswerToHomepageDraftEngine().build()
    report = CrossPlatformPromotionPlanEngine().build()
    plans = report["promotionPlans"]
    calendar = report["contentCalendarDraft"]
    platform_priority = report["platformPriority"]
    review_queue = report["promotionPlanReviewQueue"]
    summary = report["crossPlatformPromotionSummary"]

    assert report["status"] == "cross_platform_promotion_plan_ready"
    assert len(plans) >= 5
    assert summary["cross_platform_promotion_ready"] is True
    assert summary["platform_count"] >= 5
    assert summary["all_plans_need_human_review"] is True
    assert summary["auto_publish_allowed"] is False
    assert summary["write_api_called"] is False
    assert len(calendar) >= 5
    assert len(platform_priority) >= 8
    assert len(review_queue) == len(plans)

    required = {
        "plan_id",
        "draft_id",
        "platform",
        "content_format",
        "hook",
        "core_message",
        "soft_cta",
        "homepage_reference",
        "platform_tone",
        "risk_level",
        "review_status",
        "auto_publish_allowed",
    }
    expected_platforms = {"Reddit", "TikTok", "Instagram", "X", "YouTube", "Threads", "SEO", "Xiaohongshu"}
    seen_platforms = {plan["platform"] for plan in plans}
    assert expected_platforms <= seen_platforms
    for plan in plans:
        assert required <= set(plan), f"missing plan fields: {plan}"
        assert plan["soft_cta"].strip()
        assert plan["risk_level"] in {"low", "medium", "high"}
        assert plan["review_status"] == "needs_human_review"
        assert plan["auto_publish_allowed"] is False
        assert plan["real_platform_write_api_called"] is False

    for item in review_queue:
        assert item["review_status"] == "needs_human_review"
        assert item["auto_publish_allowed"] is False

    for output_name in [
        "promotion_plans.json",
        "content_calendar_draft.json",
        "platform_priority.json",
        "promotion_plan_review_queue.json",
        "cross_platform_promotion_summary.json",
    ]:
        path = PROJECT_ROOT / "runtime" / "cross_platform_promotion_plan" / output_name
        assert path.exists(), f"missing output: {output_name}"
        json.loads(path.read_text(encoding="utf-8"))

    print("cross_platform_promotion_plan_smoke_test passed")


if __name__ == "__main__":
    main()
