from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.cross_platform_promotion_plan_engine import CrossPlatformPromotionPlanEngine
from services.promotion_review_center import PromotionReviewCenter


def main() -> None:
    CrossPlatformPromotionPlanEngine().build()
    center = PromotionReviewCenter()
    report = center.build()
    items = report["promotionReviewItems"]
    summary = report["promotionReviewSummary"]

    assert report["status"] == "promotion_review_center_ready"
    assert items
    assert summary["promotion_review_center_ready"] is True
    assert summary["review_item_count"] == len(items)
    assert summary["source_counts"]["problem_candidate"] >= 1
    assert summary["source_counts"]["qualified_opportunity"] >= 1
    assert summary["source_counts"]["answer_draft"] >= 1
    assert summary["source_counts"]["promotion_plan"] >= 1
    assert set(summary["supports_decisions"]) == {"approve", "reject", "modify", "postpone"}
    assert summary["auto_publish_allowed"] is False
    assert summary["write_api_called"] is False
    assert summary["all_external_execution_allowed"] is False
    assert summary["approve_is_not_publish"] is True

    required = {
        "review_id",
        "source_type",
        "source_id",
        "workspace_id",
        "merchant_name",
        "platform",
        "item_summary",
        "risk_level",
        "review_status",
        "human_decision",
        "human_notes",
        "modified_version",
        "created_at",
        "reviewed_at",
    }
    for item in items:
        assert required <= set(item), f"missing review fields: {item}"
        assert item["review_status"] == "needs_human_review"
        assert item["human_decision"] == "pending"
        assert item["external_execution_allowed"] is False
        assert item["auto_publish_allowed"] is False
        assert item["write_api_called"] is False
        assert set(item["decision_options"]) == {"approve", "reject", "modify", "postpone"}

    target_id = items[0]["review_id"]
    updated = center.apply_decision(
        target_id,
        "modify",
        human_notes="Make the CTA softer and keep the answer first.",
        modified_version="Modified answer keeps practical steps first, then mentions the homepage only as an optional reference.",
    )
    updated_summary = updated["promotionReviewSummary"]
    assert updated_summary["decision_count"] >= 1
    assert updated_summary["modified_output_count"] >= 1
    assert updated_summary["auto_publish_allowed"] is False
    assert updated_summary["write_api_called"] is False
    modified = updated["promotionModifiedOutputs"][-1]
    assert modified["review_id"] == target_id
    assert modified["modified_version"]
    decision = updated["promotionReviewDecisions"][-1]
    assert decision["human_decision"] == "modify"
    assert decision["modified_version"] == modified["modified_version"]
    assert decision["external_execution_allowed"] is False

    for decision in ["approve", "reject", "postpone"]:
        fresh = PromotionReviewCenter().build()
        review_id = next(item["review_id"] for item in fresh["promotionReviewItems"] if item["review_status"] == "needs_human_review")
        decision_report = PromotionReviewCenter().apply_decision(review_id, decision, human_notes=f"smoke {decision}")
        last = decision_report["promotionReviewDecisions"][-1]
        assert last["human_decision"] == decision
        assert last["external_execution_allowed"] is False
        assert last["auto_publish_allowed"] is False
        assert last["write_api_called"] is False

    for output_name in [
        "promotion_review_items.json",
        "promotion_review_decisions.json",
        "promotion_modified_outputs.json",
        "promotion_review_timeline.json",
        "promotion_review_summary.json",
    ]:
        path = PROJECT_ROOT / "runtime" / "promotion_review_center" / output_name
        assert path.exists(), f"missing output: {output_name}"
        json.loads(path.read_text(encoding="utf-8"))

    print("promotion_review_center_smoke_test passed")


if __name__ == "__main__":
    main()
