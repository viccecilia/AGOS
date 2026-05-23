"""Human-gated action queue for AGOS semi-autonomous runtime."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.action_recommendation_engine import ActionRecommendationEngine
from services.runtime_persistence import utc_now_iso


VALID_DECISIONS = {"approve", "reject", "modify", "postpone"}


class ActionQueueEngine:
    """Queue action recommendations and record human decisions."""

    def __init__(self, root: str | Path = "runtime/action_queue") -> None:
        self.root = Path(root)
        self.report_path = self.root / "ACTION_QUEUE_REPORT.json"
        self.queue_path = self.root / "action_queue.json"
        self.decisions_path = self.root / "human_action_decisions.json"

    def build_queue(self, recommendations: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        recommendation_report = ActionRecommendationEngine().state()
        source_items = recommendations or recommendation_report.get("actionRecommendations", [])
        existing = {item.get("action_id"): item for item in self._load_json(self.queue_path, [])}
        queue = []
        for index, item in enumerate(source_items, start=1):
            current = existing.get(item["action_id"], {})
            queue.append(
                {
                    "queue_id": current.get("queue_id") or f"ACTION-Q-{index:04d}",
                    "action_id": item["action_id"],
                    "action_type": item["action_type"],
                    "recommendation": item["recommendation"],
                    "why_recommended": item["why_recommended"],
                    "risk_level": item["risk_level"],
                    "expected_result": item["expected_result"],
                    "recommended_platform": item["recommended_platform"],
                    "recommended_personality": item["recommended_personality"],
                    "recommended_market": item["recommended_market"],
                    "priority": item["priority"],
                    "status": current.get("status", "needs_human_approval"),
                    "human_decision": current.get("human_decision"),
                    "human_reason": current.get("human_reason", ""),
                    "human_modified_action": current.get("human_modified_action", ""),
                    "created_at": current.get("created_at", utc_now_iso()),
                    "updated_at": utc_now_iso(),
                    "execution_boundary": "local approval queue only; no external action",
                }
            )
        self._save_json(self.queue_path, queue)
        return self._report(queue)

    def approve(self, action_id: str, reason: str = "") -> dict[str, Any]:
        return self._decide(action_id, "approve", reason=reason)

    def reject(self, action_id: str, reason: str) -> dict[str, Any]:
        return self._decide(action_id, "reject", reason=reason)

    def modify(self, action_id: str, modified_action: str, reason: str = "") -> dict[str, Any]:
        return self._decide(action_id, "modify", reason=reason, modified_action=modified_action)

    def postpone(self, action_id: str, reason: str = "") -> dict[str, Any]:
        return self._decide(action_id, "postpone", reason=reason)

    def state(self) -> dict[str, Any]:
        if self.report_path.exists():
            return json.loads(self.report_path.read_text(encoding="utf-8"))
        return self.build_queue()

    def _decide(self, action_id: str, decision: str, reason: str = "", modified_action: str = "") -> dict[str, Any]:
        if decision not in VALID_DECISIONS:
            raise ValueError(f"Unsupported decision: {decision}")
        queue = self._load_json(self.queue_path, [])
        if not queue:
            queue = self.build_queue()["actionQueue"]
        for item in queue:
            if item["action_id"] == action_id:
                item["status"] = self._status_for(decision)
                item["human_decision"] = decision
                item["human_reason"] = reason
                item["human_modified_action"] = modified_action
                item["updated_at"] = utc_now_iso()
                decision_record = {
                    "decision_id": f"decision_{len(self._decisions()) + 1:04d}",
                    "action_id": action_id,
                    "queue_id": item["queue_id"],
                    "decision": decision,
                    "reason": reason,
                    "modified_action": modified_action,
                    "decided_at": utc_now_iso(),
                    "execution_boundary": "decision recorded locally; no external action executed",
                }
                decisions = self._decisions()
                decisions.append(decision_record)
                self._save_json(self.decisions_path, decisions)
                self._save_json(self.queue_path, queue)
                self._report(queue)
                return decision_record
        raise KeyError(action_id)

    def _report(self, queue: list[dict[str, Any]]) -> dict[str, Any]:
        decisions = self._decisions()
        report = {
            "report_id": "ACTION_QUEUE_REPORT",
            "created_at": utc_now_iso(),
            "status": "active",
            "scope": "local_human_gated_action_queue_only",
            "actionQueue": queue,
            "humanActionDecisions": decisions,
            "actionQueueFeed": self._feed(queue),
            "actionQueueSummary": {
                "total_actions": len(queue),
                "needs_human_approval": len([item for item in queue if item["status"] == "needs_human_approval"]),
                "approved": len([item for item in queue if item["status"] == "approved"]),
                "rejected": len([item for item in queue if item["status"] == "rejected"]),
                "modified": len([item for item in queue if item["status"] == "modified"]),
                "postponed": len([item for item in queue if item["status"] == "postponed"]),
                "decisions_recorded": len(decisions),
            },
            "safetyBoundary": "Approvals only update local state; no posting, replying, login, account creation, or platform API call is executed.",
        }
        self.root.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        return report

    @staticmethod
    def _feed(queue: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "time": item["updated_at"],
                "queue_id": item["queue_id"],
                "action_id": item["action_id"],
                "type": item["action_type"],
                "recommendation": item["recommendation"],
                "why_recommended": item["why_recommended"],
                "risk_level": item["risk_level"],
                "status": item["status"],
                "decision": item.get("human_decision") or "pending",
                "platform": item["recommended_platform"],
                "market": item["recommended_market"],
            }
            for item in queue
        ]

    def _decisions(self) -> list[dict[str, Any]]:
        return self._load_json(self.decisions_path, [])

    @staticmethod
    def _status_for(decision: str) -> str:
        return {
            "approve": "approved",
            "reject": "rejected",
            "modify": "modified",
            "postpone": "postponed",
        }[decision]

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
    result = ActionQueueEngine().build_queue()
    print(json.dumps({"status": result["status"], "queued": len(result["actionQueue"])}, indent=2))
