from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.cross_platform_promotion_plan_engine import CrossPlatformPromotionPlanEngine
from services.manual_promotion_export_pack import ManualPromotionExportPack
from services.promotion_feedback_learning import PromotionFeedbackLearning
from services.promotion_review_center import PromotionReviewCenter


def main() -> None:
    CrossPlatformPromotionPlanEngine().build()
    center = PromotionReviewCenter()
    review = center.build()
    plan_review_items = [item for item in review["promotionReviewItems"] if item["source_type"] == "promotion_plan"]
    draft_review_items = [item for item in review["promotionReviewItems"] if item["source_type"] == "answer_draft"]
    assert plan_review_items, "promotion plan review item required"
    assert draft_review_items, "answer draft review item required"

    center.apply_decision(
        plan_review_items[0]["review_id"],
        "approve",
        human_notes="Approved for manual export only. Human will copy and re-check platform rules.",
    )
    center.apply_decision(
        draft_review_items[0]["review_id"],
        "modify",
        human_notes="Make CTA softer before manual use.",
        modified_version="Manual version: answer the travel question first, keep the homepage reference optional, and avoid hard sell.",
    )
    PromotionFeedbackLearning().learn()

    pack = ManualPromotionExportPack().build()
    items = pack["manualExportItems"]
    audit = pack["manualExportAudit"]
    summary = pack["manualExportSummary"]

    assert pack["status"] == "manual_export_pack_ready"
    assert pack["human_gate_required"] is True
    assert pack["external_execution_allowed"] is False
    assert len(items) >= 2
    assert summary["manual_export_pack_ready"] is True
    assert summary["export_item_count"] == len(items)
    assert summary["approved_count"] >= 1
    assert summary["modified_count"] >= 1
    assert summary["human_gate_required"] is True
    assert summary["external_execution_allowed"] is False
    assert summary["auto_post_allowed"] is False
    assert summary["auto_reply_allowed"] is False
    assert summary["auto_dm_allowed"] is False
    assert summary["auto_follow_allowed"] is False
    assert summary["auto_like_allowed"] is False
    assert summary["write_api_called"] is False
    assert summary["credentials_touched"] is False
    assert summary["real_business_data_writeback"] is False
    assert summary["copy_ready"] is True
    assert summary["auditable"] is True
    assert summary["next_recommendation"]

    assert audit["only_human_approved_or_modified"] is True
    assert audit["every_item_has_evidence"] is True
    assert audit["every_item_has_risk_level"] is True
    assert audit["external_execution_allowed"] is False
    assert audit["write_api_called"] is False
    assert audit["credentials_touched"] is False
    assert audit["real_business_data_writeback"] is False

    required = {
        "export_id",
        "review_id",
        "source_type",
        "source_id",
        "workspace_id",
        "merchant_name",
        "platform",
        "copy_text",
        "risk_level",
        "human_approval_status",
        "human_decision",
        "source_evidence",
        "human_gate_required",
        "external_execution_allowed",
        "auto_post_allowed",
        "auto_reply_allowed",
        "auto_dm_allowed",
        "auto_follow_allowed",
        "auto_like_allowed",
        "write_api_called",
    }
    for item in items:
        assert required <= set(item), f"missing export fields: {item}"
        assert item["copy_text"]
        assert item["risk_level"] in {"low", "medium", "high"}
        assert item["human_decision"] in {"approve", "modify"}
        assert item["human_approval_status"] in {"human_approve", "human_modify"}
        assert item["source_evidence"]
        assert item["best_pattern_references"]
        assert item["human_gate_required"] is True
        assert item["external_execution_allowed"] is False
        assert item["auto_post_allowed"] is False
        assert item["auto_reply_allowed"] is False
        assert item["auto_dm_allowed"] is False
        assert item["auto_follow_allowed"] is False
        assert item["auto_like_allowed"] is False
        assert item["write_api_called"] is False
        assert item["credentials_required"] is False
        assert item["real_business_data_writeback"] is False

    for output_name in [
        "manual_export_pack.json",
        "manual_export_items.json",
        "manual_export_audit.json",
        "manual_export_summary.json",
    ]:
        path = PROJECT_ROOT / "runtime" / "manual_promotion_export_pack" / output_name
        assert path.exists(), f"missing output: {output_name}"
        json.loads(path.read_text(encoding="utf-8"))

    print("manual_promotion_export_pack_smoke_test passed")


if __name__ == "__main__":
    main()
