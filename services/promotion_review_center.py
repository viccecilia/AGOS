"""Unified human-gated review center for merchant homepage promotion actions."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from services.cross_platform_promotion_plan_engine import CrossPlatformPromotionPlanEngine
from services.runtime_persistence import utc_now_iso


DEFAULT_OUTPUT_DIR = Path("runtime/promotion_review_center")

SOURCE_PATHS = {
    "problem_candidate": Path("runtime/problem_seeker_loop/problem_candidates.json"),
    "qualified_opportunity": Path("runtime/opportunity_qualification/qualified_opportunities.json"),
    "answer_draft": Path("runtime/answer_to_homepage_drafts/answer_drafts.json"),
    "promotion_plan": Path("runtime/cross_platform_promotion_plan/promotion_plans.json"),
}


class PromotionReviewCenter:
    """Collect all promotion work into one local human review center."""

    def __init__(self, output_dir: str | Path = DEFAULT_OUTPUT_DIR) -> None:
        self.output_dir = Path(output_dir)
        self.items_path = self.output_dir / "promotion_review_items.json"
        self.decisions_path = self.output_dir / "promotion_review_decisions.json"
        self.modified_path = self.output_dir / "promotion_modified_outputs.json"
        self.timeline_path = self.output_dir / "promotion_review_timeline.json"
        self.summary_path = self.output_dir / "promotion_review_summary.json"

    def build(self) -> dict[str, Any]:
        sources = self._load_sources()
        items = self._review_items(sources)
        decisions = self._read_json(self.decisions_path, [])
        modified_outputs = self._read_json(self.modified_path, [])
        timeline = self._timeline(items, decisions)
        summary = self._summary(items, decisions, modified_outputs)
        payload = {
            "report_id": "PROMOTION_REVIEW_CENTER",
            "created_at": utc_now_iso(),
            "status": "promotion_review_center_ready",
            "phase": "MERCHANT_HOMEPAGE_GROWTH_ENGINE",
            "promotionReviewItems": items,
            "promotionReviewDecisions": decisions,
            "promotionModifiedOutputs": modified_outputs,
            "promotionReviewTimeline": timeline,
            "promotionReviewSummary": summary,
            "decisionOptions": ["approve", "reject", "modify", "postpone"],
            "safetyBoundary": "Review decisions are local governance records only. Approve does not publish, reply, DM, schedule, operate accounts, or call platform write APIs.",
        }
        self.persist(payload)
        return payload

    def state(self) -> dict[str, Any]:
        if self.summary_path.exists():
            return {
                "report_id": "PROMOTION_REVIEW_CENTER",
                "status": "promotion_review_center_ready",
                "promotionReviewItems": self._read_json(self.items_path, []),
                "promotionReviewDecisions": self._read_json(self.decisions_path, []),
                "promotionModifiedOutputs": self._read_json(self.modified_path, []),
                "promotionReviewTimeline": self._read_json(self.timeline_path, []),
                "promotionReviewSummary": self._read_json(self.summary_path, {}),
                "decisionOptions": ["approve", "reject", "modify", "postpone"],
            }
        return self.build()

    def apply_decision(
        self,
        review_id: str,
        decision: str,
        human_notes: str = "",
        modified_version: str = "",
    ) -> dict[str, Any]:
        if decision not in {"approve", "reject", "modify", "postpone"}:
            raise ValueError("decision must be approve, reject, modify, or postpone")
        payload = self.build()
        items = payload["promotionReviewItems"]
        item = next((row for row in items if row["review_id"] == review_id), None)
        if not item:
            raise ValueError(f"review_id not found: {review_id}")
        now = utc_now_iso()
        decision_record = {
            "decision_id": f"PROMO-DECISION-{len(payload['promotionReviewDecisions']) + 1:03d}",
            "review_id": review_id,
            "source_type": item["source_type"],
            "source_id": item["source_id"],
            "human_decision": decision,
            "human_notes": human_notes,
            "modified_version": modified_version if decision == "modify" else "",
            "reviewed_at": now,
            "external_execution_allowed": False,
            "auto_publish_allowed": False,
            "write_api_called": False,
        }
        decisions = payload["promotionReviewDecisions"] + [decision_record]
        modified_outputs = payload["promotionModifiedOutputs"]
        if decision == "modify":
            modified_outputs = modified_outputs + [
                {
                    "modified_id": f"PROMO-MODIFIED-{len(modified_outputs) + 1:03d}",
                    "review_id": review_id,
                    "source_type": item["source_type"],
                    "source_id": item["source_id"],
                    "modified_version": modified_version,
                    "human_notes": human_notes,
                    "created_at": now,
                    "auto_publish_allowed": False,
                }
            ]
        for row in items:
            if row["review_id"] == review_id:
                row["review_status"] = f"human_{decision}"
                row["human_decision"] = decision
                row["human_notes"] = human_notes
                row["modified_version"] = modified_version if decision == "modify" else ""
                row["reviewed_at"] = now
        timeline = self._timeline(items, decisions)
        summary = self._summary(items, decisions, modified_outputs)
        updated = {
            **payload,
            "promotionReviewItems": items,
            "promotionReviewDecisions": decisions,
            "promotionModifiedOutputs": modified_outputs,
            "promotionReviewTimeline": timeline,
            "promotionReviewSummary": summary,
        }
        self.persist(updated)
        return updated

    def persist(self, payload: dict[str, Any]) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.items_path.write_text(json.dumps(payload["promotionReviewItems"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.decisions_path.write_text(json.dumps(payload["promotionReviewDecisions"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.modified_path.write_text(json.dumps(payload["promotionModifiedOutputs"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.timeline_path.write_text(json.dumps(payload["promotionReviewTimeline"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.summary_path.write_text(json.dumps(payload["promotionReviewSummary"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    def _load_sources(self) -> dict[str, list[dict[str, Any]]]:
        if not SOURCE_PATHS["promotion_plan"].exists():
            CrossPlatformPromotionPlanEngine().build()
        return {source_type: self._read_json(path, []) for source_type, path in SOURCE_PATHS.items()}

    @staticmethod
    def _read_json(path: Path, default: Any) -> Any:
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))

    def _review_items(self, sources: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
        items = []
        for source_type, rows in sources.items():
            for row in rows:
                items.append(self._review_item(len(items) + 1, source_type, row))
        return items

    def _review_item(self, index: int, source_type: str, row: dict[str, Any]) -> dict[str, Any]:
        source_id = self._source_id(source_type, row)
        return {
            "review_id": f"PROMO-CENTER-REVIEW-{index:03d}",
            "source_type": source_type,
            "source_id": source_id,
            "workspace_id": row.get("workspace_id", ""),
            "merchant_name": row.get("merchant_name", ""),
            "platform": row.get("platform", row.get("source_platform", "")),
            "item_summary": self._summary_text(source_type, row),
            "risk_level": self._risk_level(source_type, row),
            "review_status": row.get("review_status", "needs_human_review"),
            "human_decision": "pending",
            "human_notes": "",
            "modified_version": "",
            "created_at": utc_now_iso(),
            "reviewed_at": "",
            "decision_options": ["approve", "reject", "modify", "postpone"],
            "cta_risk": self._cta_risk(row),
            "external_execution_allowed": False,
            "auto_publish_allowed": False,
            "auto_reply_allowed": False,
            "write_api_called": False,
        }

    @staticmethod
    def _source_id(source_type: str, row: dict[str, Any]) -> str:
        return {
            "problem_candidate": row.get("problem_id", ""),
            "qualified_opportunity": row.get("opportunity_id", ""),
            "answer_draft": row.get("draft_id", ""),
            "promotion_plan": row.get("plan_id", ""),
        }[source_type]

    @staticmethod
    def _summary_text(source_type: str, row: dict[str, Any]) -> str:
        if source_type == "problem_candidate":
            return row.get("question_text", "")
        if source_type == "qualified_opportunity":
            return f"{row.get('qualification_status', '')}: {row.get('question_text', '')}"
        if source_type == "answer_draft":
            return f"{row.get('direct_answer', '')} CTA: {row.get('soft_cta', '')}"
        return f"{row.get('platform', '')} {row.get('content_format', '')}: {row.get('hook', '')}"

    @staticmethod
    def _risk_level(source_type: str, row: dict[str, Any]) -> str:
        if source_type == "qualified_opportunity":
            risk = row.get("score_breakdown", {}).get("risk_level", 0)
            if risk >= 70:
                return "high"
            if risk >= 30:
                return "medium"
            return "low"
        if source_type == "answer_draft":
            return "medium" if row.get("hard_sell_risk") == "medium" else "low"
        return row.get("risk_level", "medium" if source_type == "promotion_plan" else "low")

    @staticmethod
    def _cta_risk(row: dict[str, Any]) -> str:
        text = " ".join([str(row.get("soft_cta", "")), str(row.get("core_message", "")), str(row.get("item_summary", ""))]).lower()
        if any(term in text for term in ["guaranteed", "buy now", "limited offer", "official government"]):
            return "high"
        if "homepage" in text or "reference" in text:
            return "low"
        return "none"

    @staticmethod
    def _timeline(items: list[dict[str, Any]], decisions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        timeline = [
            {
                "time": item["created_at"],
                "review_id": item["review_id"],
                "event": "review_item_created",
                "source_type": item["source_type"],
                "source_id": item["source_id"],
                "status": item["review_status"],
            }
            for item in items[:60]
        ]
        timeline.extend(
            {
                "time": decision["reviewed_at"],
                "review_id": decision["review_id"],
                "event": f"human_{decision['human_decision']}",
                "source_type": decision["source_type"],
                "source_id": decision["source_id"],
                "status": decision["human_decision"],
            }
            for decision in decisions
        )
        return timeline

    @staticmethod
    def _summary(items: list[dict[str, Any]], decisions: list[dict[str, Any]], modified_outputs: list[dict[str, Any]]) -> dict[str, Any]:
        source_counts = Counter(item["source_type"] for item in items)
        status_counts = Counter(item["review_status"] for item in items)
        decision_counts = Counter(decision["human_decision"] for decision in decisions)
        return {
            "promotion_review_center_ready": True,
            "review_item_count": len(items),
            "pending_review_count": status_counts.get("needs_human_review", 0),
            "decision_count": len(decisions),
            "modified_output_count": len(modified_outputs),
            "source_counts": dict(source_counts),
            "status_counts": dict(status_counts),
            "decision_counts": dict(decision_counts),
            "supports_decisions": ["approve", "reject", "modify", "postpone"],
            "all_external_execution_allowed": any(item["external_execution_allowed"] for item in items),
            "auto_publish_allowed": any(item["auto_publish_allowed"] for item in items),
            "write_api_called": any(item["write_api_called"] for item in items),
            "approve_is_not_publish": True,
            "recommended_next_round": "ROUND-GROWTH-PLUGIN-007 Manual Export Pack",
        }


if __name__ == "__main__":
    result = PromotionReviewCenter().build()
    print(json.dumps({"status": result["status"], "summary": result["promotionReviewSummary"]}, indent=2))
