"""Manual export pack for human-controlled merchant homepage promotion."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.cross_platform_promotion_plan_engine import CrossPlatformPromotionPlanEngine
from services.promotion_feedback_learning import PromotionFeedbackLearning
from services.promotion_review_center import PromotionReviewCenter
from services.runtime_persistence import utc_now_iso


DEFAULT_OUTPUT_DIR = Path("runtime/manual_promotion_export_pack")


class ManualPromotionExportPack:
    """Create an auditable copy-only export pack from human-reviewed promotion work."""

    def __init__(self, output_dir: str | Path = DEFAULT_OUTPUT_DIR) -> None:
        self.output_dir = Path(output_dir)
        self.pack_path = self.output_dir / "manual_export_pack.json"
        self.items_path = self.output_dir / "manual_export_items.json"
        self.audit_path = self.output_dir / "manual_export_audit.json"
        self.summary_path = self.output_dir / "manual_export_summary.json"

    def build(self) -> dict[str, Any]:
        review = PromotionReviewCenter().state()
        plan = CrossPlatformPromotionPlanEngine().state()
        feedback = PromotionFeedbackLearning().state()

        export_items = self._export_items(review, plan, feedback)
        audit = self._audit(export_items, review, plan, feedback)
        summary = self._summary(export_items, audit, feedback)
        pack = {
            "pack_id": "MANUAL_PROMOTION_EXPORT_PACK",
            "created_at": utc_now_iso(),
            "status": "manual_export_pack_ready",
            "phase": "CONTROLLED_REAL_EXTERNAL_INTERACTION_PREPARATION",
            "human_gate_required": True,
            "external_execution_allowed": False,
            "instructions": [
                "Use this pack for manual copy/paste execution only.",
                "Re-check platform rules and merchant claims before posting.",
                "Record posted_manually or rejected_by_human feedback after human action.",
                "Do not connect this pack to platform write APIs.",
            ],
            "manualExportItems": export_items,
            "manualExportAudit": audit,
            "manualExportSummary": summary,
            "safetyBoundary": "Manual export pack is a local copy-ready artifact. It never posts, replies, DMs, follows, likes, schedules, logs into platforms, writes credentials, or calls platform write APIs.",
        }
        self.persist(pack)
        return pack

    def state(self) -> dict[str, Any]:
        if self.summary_path.exists():
            return {
                "pack_id": "MANUAL_PROMOTION_EXPORT_PACK",
                "status": "manual_export_pack_ready",
                "human_gate_required": True,
                "external_execution_allowed": False,
                "manualExportItems": self._read_json(self.items_path, []),
                "manualExportAudit": self._read_json(self.audit_path, {}),
                "manualExportSummary": self._read_json(self.summary_path, {}),
            }
        return self.build()

    def persist(self, pack: dict[str, Any]) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.pack_path.write_text(json.dumps(pack, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.items_path.write_text(json.dumps(pack["manualExportItems"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.audit_path.write_text(json.dumps(pack["manualExportAudit"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.summary_path.write_text(json.dumps(pack["manualExportSummary"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    @staticmethod
    def _read_json(path: Path, default: Any) -> Any:
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))

    def _export_items(self, review: dict[str, Any], plan: dict[str, Any], feedback: dict[str, Any]) -> list[dict[str, Any]]:
        review_items = review.get("promotionReviewItems", [])
        decisions = review.get("promotionReviewDecisions", [])
        modified_outputs = review.get("promotionModifiedOutputs", [])
        promotion_plans = plan.get("promotionPlans", [])
        best_patterns = feedback.get("bestPromotionPatterns", [])

        review_by_id = {item.get("review_id"): item for item in review_items}
        plan_by_id = {item.get("plan_id"): item for item in promotion_plans}
        modified_by_review = {item.get("review_id"): item for item in modified_outputs}
        approved_decisions = [
            decision for decision in decisions
            if decision.get("human_decision") in {"approve", "modify"}
            and decision.get("source_type") in {"promotion_plan", "answer_draft"}
        ]

        export_items = []
        for decision in approved_decisions:
            review_item = review_by_id.get(decision.get("review_id"), {})
            plan_item = plan_by_id.get(decision.get("source_id"), {}) if decision.get("source_type") == "promotion_plan" else {}
            modified = modified_by_review.get(decision.get("review_id"), {})
            export_items.append(
                self._export_item(
                    index=len(export_items) + 1,
                    decision=decision,
                    review_item=review_item,
                    plan_item=plan_item,
                    modified=modified,
                    best_patterns=best_patterns,
                )
            )
        return export_items

    @staticmethod
    def _export_item(
        index: int,
        decision: dict[str, Any],
        review_item: dict[str, Any],
        plan_item: dict[str, Any],
        modified: dict[str, Any],
        best_patterns: list[dict[str, Any]],
    ) -> dict[str, Any]:
        content_source = plan_item or review_item
        copy_text = modified.get("modified_version") or plan_item.get("core_message") or review_item.get("item_summary", "")
        soft_cta = plan_item.get("soft_cta", "")
        if soft_cta and soft_cta not in copy_text:
            copy_text = f"{copy_text}\n\nSoft CTA: {soft_cta}"
        best_refs = [
            {
                "pattern_id": item.get("pattern_id"),
                "dimension": item.get("dimension"),
                "value": item.get("value"),
            }
            for item in best_patterns[:5]
        ]
        return {
            "export_id": f"MANUAL-EXPORT-{index:03d}",
            "review_id": decision.get("review_id", ""),
            "decision_id": decision.get("decision_id", ""),
            "source_type": decision.get("source_type", ""),
            "source_id": decision.get("source_id", ""),
            "workspace_id": review_item.get("workspace_id") or content_source.get("workspace_id", ""),
            "merchant_name": review_item.get("merchant_name") or content_source.get("merchant_name", ""),
            "platform": review_item.get("platform") or content_source.get("platform", ""),
            "content_format": plan_item.get("content_format") or review_item.get("source_type", ""),
            "copy_text": copy_text,
            "hook": plan_item.get("hook", ""),
            "soft_cta": soft_cta,
            "homepage_reference": plan_item.get("homepage_reference", "human_confirm_required"),
            "risk_level": review_item.get("risk_level", plan_item.get("risk_level", "medium")),
            "human_approval_status": f"human_{decision.get('human_decision', '')}",
            "human_decision": decision.get("human_decision", ""),
            "human_notes": decision.get("human_notes", ""),
            "modified_version": modified.get("modified_version", decision.get("modified_version", "")),
            "source_evidence": [
                f"review:{decision.get('review_id', '')}",
                f"source:{decision.get('source_type', '')}:{decision.get('source_id', '')}",
                "runtime/promotion_review_center/promotion_review_decisions.json",
                "runtime/cross_platform_promotion_plan/promotion_plans.json",
                "runtime/promotion_feedback_learning/best_promotion_patterns.json",
            ],
            "best_pattern_references": best_refs,
            "human_gate_required": True,
            "external_execution_allowed": False,
            "auto_post_allowed": False,
            "auto_reply_allowed": False,
            "auto_dm_allowed": False,
            "auto_follow_allowed": False,
            "auto_like_allowed": False,
            "write_api_called": False,
            "credentials_required": False,
            "real_business_data_writeback": False,
            "created_at": utc_now_iso(),
        }

    @staticmethod
    def _audit(
        export_items: list[dict[str, Any]],
        review: dict[str, Any],
        plan: dict[str, Any],
        feedback: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "audit_id": "MANUAL_PROMOTION_EXPORT_AUDIT",
            "created_at": utc_now_iso(),
            "source_files": [
                "runtime/promotion_review_center/promotion_review_items.json",
                "runtime/promotion_review_center/promotion_review_decisions.json",
                "runtime/cross_platform_promotion_plan/promotion_plans.json",
                "runtime/promotion_feedback_learning/best_promotion_patterns.json",
            ],
            "review_item_count": review.get("promotionReviewSummary", {}).get("review_item_count", 0),
            "decision_count": review.get("promotionReviewSummary", {}).get("decision_count", 0),
            "promotion_plan_count": plan.get("crossPlatformPromotionSummary", {}).get("plan_count", 0),
            "best_pattern_count": feedback.get("promotionFeedbackSummary", {}).get("best_pattern_count", 0),
            "export_item_count": len(export_items),
            "only_human_approved_or_modified": all(item["human_decision"] in {"approve", "modify"} for item in export_items),
            "every_item_has_evidence": all(bool(item["source_evidence"]) for item in export_items),
            "every_item_has_risk_level": all(bool(item["risk_level"]) for item in export_items),
            "external_execution_allowed": any(item["external_execution_allowed"] for item in export_items),
            "write_api_called": any(item["write_api_called"] for item in export_items),
            "credentials_touched": any(item["credentials_required"] for item in export_items),
            "real_business_data_writeback": any(item["real_business_data_writeback"] for item in export_items),
        }

    @staticmethod
    def _summary(export_items: list[dict[str, Any]], audit: dict[str, Any], feedback: dict[str, Any]) -> dict[str, Any]:
        platforms = sorted({item["platform"] for item in export_items if item.get("platform")})
        return {
            "manual_export_pack_ready": True,
            "export_item_count": len(export_items),
            "platforms": platforms,
            "approved_count": len([item for item in export_items if item["human_decision"] == "approve"]),
            "modified_count": len([item for item in export_items if item["human_decision"] == "modify"]),
            "best_pattern_count": feedback.get("promotionFeedbackSummary", {}).get("best_pattern_count", 0),
            "human_gate_required": True,
            "external_execution_allowed": audit.get("external_execution_allowed", True),
            "auto_post_allowed": any(item["auto_post_allowed"] for item in export_items),
            "auto_reply_allowed": any(item["auto_reply_allowed"] for item in export_items),
            "auto_dm_allowed": any(item["auto_dm_allowed"] for item in export_items),
            "auto_follow_allowed": any(item["auto_follow_allowed"] for item in export_items),
            "auto_like_allowed": any(item["auto_like_allowed"] for item in export_items),
            "write_api_called": audit.get("write_api_called", True),
            "credentials_touched": audit.get("credentials_touched", True),
            "real_business_data_writeback": audit.get("real_business_data_writeback", True),
            "copy_ready": len(export_items) > 0 and audit.get("every_item_has_evidence", False),
            "auditable": audit.get("every_item_has_evidence", False) and audit.get("only_human_approved_or_modified", False),
            "next_recommendation": "Manually post selected export items, then record posted_manually, ignored, liked, replied, saved, shared, or rejected_by_human feedback for the next learning loop.",
        }


if __name__ == "__main__":
    result = ManualPromotionExportPack().build()
    print(json.dumps({"status": result["status"], "summary": result["manualExportSummary"]}, indent=2))
