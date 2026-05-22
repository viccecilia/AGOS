"""Local AGOS Runtime Engine.

This engine runs only local state transitions and file writes. It never logs in
to platforms, posts content, replies to users, registers accounts, or calls
external platform APIs.
"""

from __future__ import annotations

from typing import Any

from services.human_review_runtime import HumanReviewRuntime
from services.runtime_memory_deposit import RuntimeMemoryDeposit
from services.runtime_persistence import RuntimePersistence
from services.runtime_queue import RuntimeQueue
from services.runtime_state_machine import RuntimeStateMachine


RUNTIME_STATUSES = {
    "idle",
    "running",
    "paused",
    "stopped",
    "needs_human_review",
    "needs_code_check",
    "needs_runtime_validation",
}


class RuntimeEngine:
    def __init__(
        self,
        persistence: RuntimePersistence | None = None,
        queue: RuntimeQueue | None = None,
        review: HumanReviewRuntime | None = None,
        memory: RuntimeMemoryDeposit | None = None,
    ) -> None:
        self.persistence = persistence or RuntimePersistence()
        self.queue = queue or RuntimeQueue(self.persistence.root)
        self.review = review or HumanReviewRuntime(self.persistence.root)
        self.memory = memory or RuntimeMemoryDeposit(self.persistence.root)

    def initialize(
        self,
        workspace: str = "jag_app_growth",
        industry_pack: str = "Travel Pack",
        cycle: str = "CYCLE-0001",
    ) -> dict[str, Any]:
        machine = RuntimeStateMachine()
        state = {
            "status": "idle",
            "workspace": workspace,
            "industry_pack": industry_pack,
            "cycle": cycle,
            "current_stage": machine.current_stage,
            "next_stage": machine.next_stage,
            "pipeline": machine.to_pipeline(),
            "current_event": None,
            "current_error": None,
            "human_review": None,
            "learning_result": None,
            "runtime_feed": [],
            "correction_alerts": [],
            "review_queue": [],
            "learning_deposits": [],
        }
        saved = self.persistence.save_state(state)
        self._event(saved, "initialize", "Runtime initialized")
        return self.persistence.save_state({**saved, "runtime_feed": self.persistence.load_events()})

    def start(self) -> dict[str, Any]:
        state = self._state_or_default()
        state["status"] = "running"
        state["current_error"] = None
        state["current_event"] = "runtime_started"
        self.queue.enqueue(
            {
                "queue_id": f"{state['cycle']}_analyze",
                "type": "待分析",
                "payload": {
                    "workspace": state["workspace"],
                    "cycle": state["cycle"],
                    "stage": state["current_stage"],
                },
            }
        )
        self._event(state, "start", "Runtime entered running state")
        return self._save_with_related(state)

    def stop(self) -> dict[str, Any]:
        state = self._state_or_default()
        state["status"] = "stopped"
        state["current_event"] = "runtime_stopped"
        self._event(state, "stop", "Runtime stopped locally")
        return self._save_with_related(state)

    def pause(self) -> dict[str, Any]:
        state = self._state_or_default()
        state["status"] = "paused"
        state["current_event"] = "runtime_paused"
        machine = RuntimeStateMachine.from_pipeline(state["current_stage"], state.get("pipeline"))
        machine.pause_current()
        state["pipeline"] = machine.to_pipeline()
        self._event(state, "pause", "Runtime paused")
        return self._save_with_related(state)

    def advance(self) -> dict[str, Any]:
        state = self._state_or_default()
        if state["status"] not in {"running", "needs_human_review"}:
            raise ValueError("Runtime must be running or at human review to advance")
        machine = RuntimeStateMachine.from_pipeline(state["current_stage"], state.get("pipeline"))
        if machine.current_stage == "Human Review":
            state["status"] = "needs_human_review"
            review_item = self.review.request_review(
                {
                    "workspace": state["workspace"],
                    "cycle": state["cycle"],
                    "stage": machine.current_stage,
                    "content": {"strategy": "rescue-first helpful answer"},
                }
            )
            state["human_review"] = review_item
            state["current_event"] = "human_review_required"
            self._event(state, "human_review", "Runtime waiting for human review")
            return self._save_with_related(state)
        next_stage = machine.complete_current()
        state["current_stage"] = next_stage
        state["next_stage"] = machine.next_stage
        state["pipeline"] = machine.to_pipeline()
        state["current_event"] = f"stage_advanced_to_{next_stage}"
        self._event(state, next_stage, f"Runtime advanced to {next_stage}")
        if next_stage == "Deposit":
            state["learning_deposits"] = self.memory.deposit_runtime_result(state)
            state["learning_result"] = "Runtime deposited local memory results"
        return self._save_with_related(state)

    def fail_current(self, error: str, status: str = "needs_code_check") -> dict[str, Any]:
        if status not in RUNTIME_STATUSES:
            raise ValueError(f"Invalid runtime status: {status}")
        state = self._state_or_default()
        machine = RuntimeStateMachine.from_pipeline(state["current_stage"], state.get("pipeline"))
        machine.fail_current(error)
        state["status"] = status
        state["pipeline"] = machine.to_pipeline()
        state["current_error"] = error
        state["current_event"] = "stage_failed"
        self._event(state, "failure", error)
        return self._save_with_related(state)

    def approve_review(self, review_id: str) -> dict[str, Any]:
        state = self._state_or_default()
        approved = self.review.approve(review_id)
        machine = RuntimeStateMachine.from_pipeline(state["current_stage"], state.get("pipeline"))
        state["current_stage"] = machine.approve_human_gate()
        state["next_stage"] = machine.next_stage
        state["pipeline"] = machine.to_pipeline()
        state["status"] = "running"
        state["human_review"] = approved
        state["current_event"] = "human_review_approved"
        self._event(state, "approve", "Human review approved")
        return self._save_with_related(state)

    def reject_review(self, review_id: str, reason: str) -> dict[str, Any]:
        state = self._state_or_default()
        rejected = self.review.reject(review_id, reason)
        state["status"] = "needs_human_review"
        state["human_review"] = rejected
        state["current_error"] = reason
        self._event(state, "reject", reason)
        return self._save_with_related(state)

    def modify_review(self, review_id: str, modified_content: dict[str, Any]) -> dict[str, Any]:
        state = self._state_or_default()
        modified = self.review.modify(review_id, modified_content)
        state["status"] = "needs_human_review"
        state["human_review"] = modified
        self._event(state, "modify", "Human review requested modification")
        return self._save_with_related(state)

    def current_state(self) -> dict[str, Any]:
        return self._save_with_related(self._state_or_default())

    def _state_or_default(self) -> dict[str, Any]:
        state = self.persistence.load_state()
        if not state:
            state = self.initialize()
        return state

    def _save_with_related(self, state: dict[str, Any]) -> dict[str, Any]:
        state["runtime_feed"] = self.persistence.load_events()
        state["runtime_queue"] = self.queue.list()
        state["review_queue"] = self.review.pending()
        state["learning_deposits"] = self.memory.list(state.get("workspace", "jag_app_growth"))
        return self.persistence.save_state(state)

    def _event(self, state: dict[str, Any], event: str, result: str) -> dict[str, Any]:
        return self.persistence.append_event(
            {
                "workspace": state.get("workspace", "jag_app_growth"),
                "industry_pack": state.get("industry_pack", "Travel Pack"),
                "cycle": state.get("cycle", "CYCLE-0001"),
                "stage": state.get("current_stage", "Scout"),
                "event": event,
                "result": result,
            }
        )
