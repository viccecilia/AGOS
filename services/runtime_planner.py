"""Runtime planner for AGOS semi-autonomous runtime."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.action_queue_engine import ActionQueueEngine
from services.runtime_persistence import utc_now_iso
from services.runtime_priority_engine import RuntimePriorityEngine


class RuntimePlanner:
    """Create a local operating plan from human-gated action queue state."""

    def __init__(self, root: str | Path = "runtime/runtime_plans") -> None:
        self.root = Path(root)
        self.report_path = self.root / "RUNTIME_ACTION_PLAN.json"
        self.plan_path = self.root / "runtime_plan.json"
        self.feed_path = self.root / "runtime_plan_feed.json"

    def plan(self) -> dict[str, Any]:
        queue_report = ActionQueueEngine().state()
        priority = RuntimePriorityEngine().state()
        queue = queue_report.get("actionQueue", [])
        allowed = [item for item in queue if item.get("status") in {"approved", "modified"}]
        pending = [item for item in queue if item.get("status") == "needs_human_approval"]
        plan_items = self._plan_items(allowed, pending, priority)
        plan = {
            "report_id": "RUNTIME_ACTION_PLAN",
            "created_at": utc_now_iso(),
            "status": "ready_for_human_review" if plan_items else "waiting_for_approval",
            "scope": "local_runtime_plan_only",
            "todayOperationPlan": plan_items,
            "todayPlatformFocus": self._platform_focus(queue, priority),
            "todayContentRhythm": self._content_rhythm(plan_items, pending),
            "todayReplyPriority": self._reply_priority(queue, priority),
            "runtimePlanFeed": self._feed(plan_items),
            "runtimePlanSummary": {
                "planned_actions": len(plan_items),
                "pending_approval": len(pending),
                "approved_or_modified": len(allowed),
                "top_platform": priority.get("prioritySummary", {}).get("top_platform", "reddit"),
                "execution_boundary": "local plan only; no external action",
            },
            "safetyBoundary": "The plan does not post, reply, log in, register accounts, or call platform APIs.",
        }
        self.persist(plan)
        return plan

    def state(self) -> dict[str, Any]:
        if self.report_path.exists():
            return json.loads(self.report_path.read_text(encoding="utf-8"))
        return self.plan()

    def persist(self, plan: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.plan_path.write_text(
            json.dumps(plan["todayOperationPlan"], ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        self.feed_path.write_text(json.dumps(plan["runtimePlanFeed"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    @staticmethod
    def _plan_items(allowed: list[dict[str, Any]], pending: list[dict[str, Any]], priority: dict[str, Any]) -> list[dict[str, Any]]:
        source = allowed or pending
        items = []
        for rank, action in enumerate(source, start=1):
            wait_gate = action.get("status") == "needs_human_approval"
            items.append(
                {
                    "plan_id": f"PLAN-{rank:04d}",
                    "action_id": action["action_id"],
                    "action_type": action["action_type"],
                    "planned_action": action.get("human_modified_action") or action["recommendation"],
                    "platform": action["recommended_platform"],
                    "market": action["recommended_market"],
                    "personality": action["recommended_personality"],
                    "priority": action["priority"],
                    "approval_state": action["status"],
                    "today_sequence": rank,
                    "time_block": RuntimePlanner._time_block(action["action_type"], rank),
                    "why_this_plan": RuntimePlanner._why(action, priority, wait_gate),
                    "execution_mode": "wait_for_human_approval" if wait_gate else "local_plan_ready",
                    "execution_boundary": "local plan only; no external action",
                }
            )
        return items

    @staticmethod
    def _platform_focus(queue: list[dict[str, Any]], priority: dict[str, Any]) -> dict[str, Any]:
        top = priority.get("prioritySummary", {}).get("top_platform", "reddit")
        platforms = sorted({item.get("recommended_platform", top) for item in queue})
        return {
            "primary_platform": top,
            "supporting_platforms": platforms,
            "reason": f"{top} is the current priority leader; other platforms stay secondary until approval.",
        }

    @staticmethod
    def _content_rhythm(plan_items: list[dict[str, Any]], pending: list[dict[str, Any]]) -> dict[str, Any]:
        content_count = len([item for item in plan_items if item["action_type"] in {"today_content", "today_trend"}])
        return {
            "rhythm": "one_content_one_reply_block" if content_count else "approval_first",
            "planned_content_blocks": content_count,
            "approval_waiting": len(pending),
            "reason": "Keep cadence small while human approval is required.",
        }

    @staticmethod
    def _reply_priority(queue: list[dict[str, Any]], priority: dict[str, Any]) -> dict[str, Any]:
        reply_items = [item for item in queue if item.get("action_type") == "today_reply"]
        return {
            "priority": "high" if reply_items else "watch",
            "target": priority.get("prioritySummary", {}).get("top_question", "Tokyo transport anxiety"),
            "reply_count": len(reply_items),
            "reason": "Replies remain human-gated and focus on the top question.",
        }

    @staticmethod
    def _feed(plan_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "time": utc_now_iso(),
                "plan_id": item["plan_id"],
                "action_type": item["action_type"],
                "planned_action": item["planned_action"],
                "platform": item["platform"],
                "priority": item["priority"],
                "time_block": item["time_block"],
                "approval_state": item["approval_state"],
                "why_this_plan": item["why_this_plan"],
                "status": item["execution_mode"],
            }
            for item in plan_items
        ]

    @staticmethod
    def _time_block(action_type: str, rank: int) -> str:
        if action_type == "today_content":
            return "morning_content_planning"
        if action_type == "today_reply":
            return "midday_reply_review"
        if action_type == "today_platform":
            return "platform_focus_setup"
        if action_type == "today_trend":
            return "afternoon_trend_watch"
        return f"block_{rank}"

    @staticmethod
    def _why(action: dict[str, Any], priority: dict[str, Any], wait_gate: bool) -> str:
        suffix = " Human approval is still required." if wait_gate else " Human approval is already recorded."
        return f"{action.get('why_recommended', '')} Top platform is {priority.get('prioritySummary', {}).get('top_platform', 'unknown')}." + suffix


if __name__ == "__main__":
    result = RuntimePlanner().plan()
    print(json.dumps({"status": result["status"], "planned": len(result["todayOperationPlan"])}, indent=2))
