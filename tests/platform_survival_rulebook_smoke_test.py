from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.external_action_sandbox import ExternalActionSandbox
from services.platform_survival_rulebook import PlatformSurvivalRulebook
from services.promotion_review_center import PromotionReviewCenter


def main() -> None:
    PromotionReviewCenter().build()
    ExternalActionSandbox().build()

    review_items = [
        {
            "review_id": "RULE-REVIEW-REDDIT-001",
            "source_type": "promotion_plan",
            "source_id": "PLAN-REDDIT-SPAM",
            "workspace_id": "jag_app_growth",
            "merchant_name": "Japan AI Guide App",
            "platform": "Reddit",
            "item_summary": "Reply with useful Tokyo station advice, then buy now with a limited offer and DM me.",
            "risk_level": "high",
            "review_status": "needs_human_review",
            "auto_publish_allowed": False,
            "auto_reply_allowed": False,
            "external_execution_allowed": False,
            "write_api_called": False,
        },
        {
            "review_id": "RULE-REVIEW-X-001",
            "source_type": "promotion_plan",
            "source_id": "PLAN-X-SAFE",
            "workspace_id": "jag_app_growth",
            "merchant_name": "Japan AI Guide App",
            "platform": "X",
            "item_summary": "Short practical note about Haneda arrival timing with an optional reference.",
            "risk_level": "low",
            "review_status": "needs_human_review",
            "auto_publish_allowed": False,
            "auto_reply_allowed": False,
            "external_execution_allowed": False,
            "write_api_called": False,
        },
    ]
    external_actions = [
        {
            "external_action_id": "EXT-ACTION-RULE-REDDIT",
            "external_action_type": "external_reply",
            "suggested_action": "Post a Reddit reply with a homepage link and official partner claim.",
            "why_suggested": "Promote homepage to Reddit users.",
            "target_platform": "Reddit",
            "target_market": "Japan",
            "risk_level": "medium",
            "status": "waiting_human_approval",
            "human_gate_status": "required",
            "external_execution_allowed": False,
            "write_api_call_attempted": False,
            "write_api_call_allowed": False,
        },
        {
            "external_action_id": "EXT-ACTION-RULE-TIKTOK",
            "external_action_type": "external_content_publish",
            "suggested_action": "Prepare a TikTok hook about airport transfer mistakes and ask viewers to save this.",
            "why_suggested": "Travelers need short guidance.",
            "target_platform": "TikTok",
            "target_market": "Japan",
            "risk_level": "low",
            "status": "waiting_human_approval",
            "human_gate_status": "required",
            "external_execution_allowed": False,
            "write_api_call_attempted": False,
            "write_api_call_allowed": False,
        },
    ]

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "platform_survival_rulebook"
        report = PlatformSurvivalRulebook(root).build(review_items=review_items, external_actions=external_actions)

        assert report["status"] == "platform_survival_rulebook_ready"
        rules = report["platformSurvivalRules"]
        assert {"Reddit", "X", "TikTok", "Instagram", "YouTube", "Threads"} <= set(rules)
        for platform, rule in rules.items():
            assert rule["forbidden_patterns"], f"missing forbidden patterns for {platform}"
            assert rule["safe_cta"], f"missing safe CTA for {platform}"
            assert rule["posting_cadence"], f"missing cadence for {platform}"
            assert rule["community_risk"], f"missing community risk for {platform}"
            assert rule["strong_marketing_allowed_by_default"] is False

        governed_reviews = report["governedPromotionReviewItems"]
        governed_actions = report["governedExternalActionQueue"]
        summary = report["platformSurvivalRulebookSummary"]
        risk_review = report["platformSurvivalRiskReview"]

        reddit_review = next(item for item in governed_reviews if item["platform_survival_platform"] == "Reddit")
        assert reddit_review["platform_survival_status"] == "rejected"
        assert {"buy now", "limited offer", "dm me"} <= set(reddit_review["forbidden_pattern_hits"])
        assert reddit_review["survival_rejected"] is True
        assert reddit_review["auto_publish_allowed"] is False
        assert reddit_review["auto_reply_allowed"] is False
        assert reddit_review["external_execution_allowed"] is False

        reddit_action = next(item for item in governed_actions if item["target_platform"] == "Reddit")
        assert reddit_action["platform_survival_status"] == "rejected"
        assert "official partner" in reddit_action["forbidden_pattern_hits"]
        assert reddit_action["status"] == "rejected"
        assert reddit_action["external_execution_allowed"] is False
        assert reddit_action["write_api_call_allowed"] is False

        safe_action = next(item for item in governed_actions if item["target_platform"] == "TikTok")
        assert safe_action["platform_survival_status"] == "safe_with_review"
        assert safe_action["survival_review_required"] is True
        assert safe_action["external_execution_allowed"] is False

        assert summary["platform_survival_rulebook_ready"] is True
        assert summary["high_risk_downgraded_or_rejected"] is True
        assert summary["reddit_strong_marketing_blocked"] is True
        assert summary["auto_publish_allowed"] is False
        assert summary["auto_reply_allowed"] is False
        assert summary["external_execution_allowed"] is False
        assert summary["write_api_called"] is False
        assert risk_review["rejected_count"] >= 2

        for output_name in [
            "platform_survival_rules.json",
            "governed_promotion_review_items.json",
            "governed_external_action_queue.json",
            "platform_survival_risk_review.json",
            "PLATFORM_SURVIVAL_RULEBOOK_REPORT.json",
        ]:
            path = root / output_name
            assert path.exists(), f"missing output: {output_name}"
            json.loads(path.read_text(encoding="utf-8"))

    print("platform_survival_rulebook_smoke_test passed")


if __name__ == "__main__":
    main()
