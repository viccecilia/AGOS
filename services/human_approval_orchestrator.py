"""Unified human approval orchestration for AGOS semi-autonomous runtime."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.action_queue_engine import ActionQueueEngine
from services.human_review_runtime import HumanReviewRuntime
from services.runtime_correction_engine import RuntimeCorrectionEngine
from services.runtime_persistence import utc_now_iso


VALID_UNIFIED_DECISIONS = {"approve", "reject", "modify", "postpone"}


class HumanApprovalOrchestrator:
    """Unify review, action, and correction approval queues."""

    def __init__(self, root: str | Path = "runtime/human_approval") -> None:
        self.root = Path(root)
        self.report_path = self.root / "HUMAN_APPROVAL_ORCHESTRATION_REPORT.json"
        self.queue_path = self.root / "unified_approval_queue.json"
        self.timeline_path = self.root / "UNIFIED_APPROVAL_TIMELINE.json"
        self.decisions_path = self.root / "unified_approval_decisions.json"

    def orchestrate(
        self,
        review_queue: list[dict[str, Any]] | None = None,
        action_queue: list[dict[str, Any]] | None = None,
        correction_queue: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        reviews = review_queue if review_queue is not None else HumanReviewRuntime().list()
        actions = action_queue if action_queue is not None else ActionQueueEngine().state().get("actionQueue", [])
        corrections = correction_queue if correction_queue is not None else RuntimeCorrectionEngine().list()

        unified_queue = (
            self._review_items(reviews)
            + self._action_items(actions)
            + self._correction_items(corrections)
        )
        timeline = self._timeline(unified_queue)
        report = {
            "report_id": "HUMAN_APPROVAL_ORCHESTRATION_REPORT",
            "created_at": utc_now_iso(),
            "status": "active",
            "scope": "local_unified_human_approval_only",
            "unifiedApprovalQueue": unified_queue,
            "unifiedApprovalTimeline": timeline,
            "approvalSummary": {
                "total_items": len(unified_queue),
                "review_queue_items": len([item for item in unified_queue if item["queue_type"] == "review"]),
                "action_queue_items": len([item for item in unified_queue if item["queue_type"] == "action"]),
                "correction_queue_items": len([item for item in unified_queue if item["queue_type"] == "correction"]),
                "needs_human_approval": len([item for item in unified_queue if item["status"] in {"needs_human_review", "needs_human_approval"}]),
                "approved": len([item for item in unified_queue if item["status"] == "approved"]),
                "rejected": len([item for item in unified_queue if item["status"] == "rejected"]),
                "modified": len([item for item in unified_queue if item["status"] == "modified"]),
                "postponed": len([item for item in unified_queue if item["status"] == "postponed"]),
                "decisions_recorded": len(self._decisions()),
            },
            "safetyBoundary": "Unified approval only records local human decisions; no posting, replying, login, account creation, or platform API call is executed.",
        }
        self.persist(report)
        return report

    def decide(
        self,
        queue_type: str,
        target_id: str,
        decision: str,
        reason: str = "",
        modified_content: Any = None,
    ) -> dict[str, Any]:
        if decision not in VALID_UNIFIED_DECISIONS:
            raise ValueError(f"Unsupported unified approval decision: {decision}")
        if queue_type == "action":
            record = self._decide_action(target_id, decision, reason, modified_content)
        elif queue_type == "review":
            record = self._decide_review(target_id, decision, reason, modified_content)
        elif queue_type == "correction":
            record = self._decide_correction(target_id, decision, reason, modified_content)
        else:
            raise ValueError(f"Unsupported queue type: {queue_type}")

        decision_record = {
            "unified_decision_id": f"unified_decision_{len(self._decisions()) + 1:04d}",
            "queue_type": queue_type,
            "target_id": target_id,
            "decision": decision,
            "reason": reason,
            "modified_content": modified_content or "",
            "source_record": record,
            "decided_at": utc_now_iso(),
            "execution_boundary": "decision recorded locally; no external action executed",
        }
        decisions = self._decisions()
        decisions.append(decision_record)
        self._save_json(self.decisions_path, decisions)
        self.orchestrate()
        return decision_record

    def state(self) -> dict[str, Any]:
        if self.report_path.exists():
            return json.loads(self.report_path.read_text(encoding="utf-8"))
        return self.orchestrate()

    def persist(self, report: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.queue_path.write_text(json.dumps(report["unifiedApprovalQueue"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.timeline_path.write_text(json.dumps(report["unifiedApprovalTimeline"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    @staticmethod
    def _review_items(reviews: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "unified_id": f"APPROVAL-REVIEW-{index:04d}",
                "queue_type": "review",
                "target_id": item.get("review_id", f"review_{index:04d}"),
                "title": item.get("target_type", "review"),
                "description": item.get("ai_reason", "Human review required before runtime can continue."),
                "risk_level": item.get("risk_level", "medium"),
                "status": item.get("status", "needs_human_review"),
                "workspace": item.get("workspace", "JAG-LAB"),
                "platform": item.get("source_platform", item.get("platform", "Local Runtime")),
                "market": item.get("country", item.get("market", "local")),
                "created_at": item.get("created_at", item.get("generated_at", utc_now_iso())),
                "required_decisions": ["approve", "reject", "modify"],
                "source": item,
            }
            for index, item in enumerate(reviews, start=1)
        ]

    @staticmethod
    def _action_items(actions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "unified_id": f"APPROVAL-ACTION-{index:04d}",
                "queue_type": "action",
                "target_id": item.get("action_id", f"action_{index:04d}"),
                "title": item.get("action_type", "action"),
                "description": item.get("why_recommended", item.get("recommendation", "")),
                "risk_level": item.get("risk_level", "medium"),
                "status": item.get("status", "needs_human_approval"),
                "workspace": item.get("workspace", "JAG-LAB"),
                "platform": item.get("recommended_platform", item.get("platform", "Local Runtime")),
                "market": item.get("recommended_market", item.get("market", "local")),
                "created_at": item.get("created_at", item.get("updated_at", utc_now_iso())),
                "required_decisions": ["approve", "reject", "modify", "postpone"],
                "source": item,
            }
            for index, item in enumerate(actions, start=1)
        ]

    @staticmethod
    def _correction_items(corrections: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "unified_id": f"APPROVAL-CORRECTION-{index:04d}",
                "queue_type": "correction",
                "target_id": item.get("correction_id", f"correction_{index:04d}"),
                "title": item.get("target_type", "correction"),
                "description": item.get("reason", "Human correction should be reviewed before learning memory changes."),
                "risk_level": item.get("risk_level", "medium"),
                "status": item.get("status", "needs_human_review"),
                "workspace": item.get("workspace", "JAG-LAB"),
                "platform": item.get("platform", "Local Runtime"),
                "market": item.get("market", "local"),
                "created_at": item.get("created_at", utc_now_iso()),
                "required_decisions": ["approve", "reject", "modify"],
                "source": item,
            }
            for index, item in enumerate(corrections, start=1)
        ]

    @staticmethod
    def _timeline(unified_queue: list[dict[str, Any]]) -> list[dict[str, Any]]:
        def sort_key(item: dict[str, Any]) -> str:
            return str(item.get("created_at", ""))

        return [
            {
                "time": item["created_at"],
                "unified_id": item["unified_id"],
                "queue_type": item["queue_type"],
                "target_id": item["target_id"],
                "title": item["title"],
                "status": item["status"],
                "risk_level": item["risk_level"],
                "human_action_needed": item["status"] in {"needs_human_review", "needs_human_approval"},
                "why": item["description"],
            }
            for item in sorted(unified_queue, key=sort_key)
        ]

    @staticmethod
    def _decide_action(target_id: str, decision: str, reason: str, modified_content: Any) -> dict[str, Any]:
        engine = ActionQueueEngine()
        if decision == "approve":
            return engine.approve(target_id, reason=reason)
        if decision == "reject":
            return engine.reject(target_id, reason=reason)
        if decision == "modify":
            return engine.modify(target_id, str(modified_content or ""), reason=reason)
        return engine.postpone(target_id, reason=reason)

    @staticmethod
    def _decide_review(target_id: str, decision: str, reason: str, modified_content: Any) -> dict[str, Any]:
        engine = HumanReviewRuntime()
        if decision == "approve":
            return engine.approve(target_id)
        if decision == "reject":
            return engine.reject(target_id, reason=reason)
        if decision == "modify":
            payload = modified_content if isinstance(modified_content, dict) else {"modified_content": modified_content or ""}
            return engine.modify(target_id, payload)
        raise ValueError("Review queue does not support postpone")

    @staticmethod
    def _decide_correction(target_id: str, decision: str, reason: str, modified_content: Any) -> dict[str, Any]:
        payload = {
            "correction_id": target_id,
            "target_type": "unified_correction",
            "target_id": target_id,
            "reason": reason or f"Unified correction decision: {decision}",
            "rejected_learning": {"modified_content": modified_content or ""},
        }
        if decision == "reject":
            return RuntimeCorrectionEngine().reject(payload)
        record = {
            **payload,
            "status": "approved" if decision == "approve" else "modified",
            "created_at": utc_now_iso(),
        }
        items = RuntimeCorrectionEngine().list()
        items.append(record)
        path = RuntimeCorrectionEngine().path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(items, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        return record

    def _decisions(self) -> list[dict[str, Any]]:
        return self._load_json(self.decisions_path, [])

    @staticmethod
    def _load_json(path: Path, default: Any) -> Any:
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _save_json(path: Path, payload: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


if __name__ == "__main__":
    result = HumanApprovalOrchestrator().orchestrate()
    print(json.dumps({"status": result["status"], "items": result["approvalSummary"]["total_items"]}, indent=2))
