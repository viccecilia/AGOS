"""Local AGOS Runtime Engine.

This engine runs only local state transitions and file writes. It never logs in
to platforms, posts content, replies to users, registers accounts, or calls
external platform APIs.
"""

from __future__ import annotations

from typing import Any

from services.human_review_runtime import HumanReviewRuntime
from services.opportunity_scoring_engine import OpportunityScoringEngine
from services.platform_personality_engine import PlatformPersonalityEngine
from services.runtime_correction_engine import RuntimeCorrectionEngine
from services.runtime_memory_deposit import RuntimeMemoryDeposit
from services.runtime_persistence import RuntimePersistence
from services.runtime_queue import RuntimeQueue
from services.runtime_review_session import RuntimeReviewSession
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
        review_session: RuntimeReviewSession | None = None,
    ) -> None:
        self.persistence = persistence or RuntimePersistence()
        self.queue = queue or RuntimeQueue(self.persistence.root)
        self.review = review or HumanReviewRuntime(self.persistence.root)
        self.memory = memory or RuntimeMemoryDeposit(self.persistence.root)
        self.scoring = OpportunityScoringEngine()
        self.personality = PlatformPersonalityEngine()
        self.correction = RuntimeCorrectionEngine(self.persistence.root)
        self.review_session = review_session or RuntimeReviewSession()

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

    def run_training_cycle(self, question: dict | None = None, platforms: list[str] | None = None) -> dict[str, Any]:
        question = question or {
            "question_id": "jag_lab_tokyo_transport_001",
            "platform": "reddit",
            "platforms": ["reddit", "tiktok", "x"],
            "market": "Japan",
            "question_text": "I am confused about Tokyo train transfers and worried I will get lost. What should I check first?",
            "pain_points": ["Tokyo transport anxiety", "first trip confusion"],
        }
        platforms = platforms or ["reddit", "tiktok", "x"]
        state = self.initialize(workspace="JAG-LAB", industry_pack="Travel Pack / Lab", cycle="JAG-LAB-CYCLE-0001")
        state = self.start()

        explanations: list[dict[str, Any]] = []
        score = self.scoring.score(question).to_dict()
        style_plans = [self.personality.generate_style_plan(platform, question) for platform in platforms]
        generated = {
            "reply_text": "Start with station names, transfer count, platform number, and a backup route. Avoid over-planning; keep the first route simple.",
            "hook": style_plans[1]["hook"],
            "strategy": "rescue-first helpful answer",
        }
        alerts = self.correction.detect_mislearning(generated)
        if score["verdict"] == "low_value":
            alerts.append(
                {
                    "issue": "错误高价值判断",
                    "status": "needs_human_review",
                    "severity": "medium",
                    "signal": "Opportunity score is low; do not reply by default.",
                    "action": "Reject high-value label.",
                }
            )
        correction_record = self.correction.reject(
            {
                "target_type": "platform_style",
                "target_id": question["question_id"],
                "reason": "训练样例：如果平台风格过度营销，必须拒绝错误学习。",
                "rejected_learning": {"platform": "reddit", "bad_style": "short promotional CTA"},
            }
        )
        alerts.append(correction_record)

        for stage in ["Scout", "Collect", "Analyze", "Classify", "Prioritize", "Strategy", "Generate", "Human Review", "Learn", "Deposit"]:
            explanation = self._training_explanation(stage, question, score, style_plans, generated)
            explanations.append(explanation)
            self._event(state, stage, explanation["why"])
            if stage == "Analyze":
                state["opportunity_score"] = score
            if stage == "Strategy":
                state["platform_personality"] = style_plans
            if stage == "Human Review":
                state["status"] = "needs_human_review"
                state["human_review"] = self.review.request_review(
                    {
                        "workspace": "JAG-LAB",
                        "cycle": state["cycle"],
                        "stage": "Human Review",
                        "target_type": "runtime_training",
                        "source_platform": question.get("platform", "reddit"),
                        "country": question.get("market", "Japan"),
                        "language": "en",
                        "pain_point": ", ".join(question.get("pain_points", [])),
                        "ai_reason": "Opportunity score and platform style plan require human approval before AGOS learns this answer branch.",
                        "risk_level": "medium",
                        "content": generated,
                    }
                )
            if stage == "Learn":
                state["status"] = "running"
                state["mislearning_alerts"] = alerts
                state["correction_alerts"] = alerts
            if stage == "Deposit":
                state["runtime_intelligence"] = {
                    "best_answer": [generated["reply_text"]],
                    "best_hook": [style_plans[1]["hook"]],
                    "best_platform_style": style_plans,
                    "best_timing": ["manual review before posting"],
                    "failed_strategy": ["short promotional CTA on Reddit"],
                    "failed_reply": ["generic marketing reply"],
                    "failed_hook": ["same hook repeated"],
                }
                state["learning_deposits"] = self.memory.deposit_runtime_result(state)
        state["training_explanations"] = explanations
        state["runtime_review_report"] = self.review_session.generate(state, alerts)
        state["current_stage"] = "Deposit"
        state["next_stage"] = None
        state["pipeline"] = [
            {
                "id": stage,
                "label": stage,
                "status": "current" if stage == "Deposit" else "done",
                "note": RuntimeStateMachine._stage_note(stage),
            }
            for stage in ["Scout", "Collect", "Analyze", "Classify", "Prioritize", "Strategy", "Generate", "Human Review", "Learn", "Deposit"]
        ]
        state["current_event"] = "runtime_training_cycle_completed"
        return self._save_with_related(state)

    @staticmethod
    def _training_explanation(stage: str, question: dict, score: dict, style_plans: list[dict], generated: dict) -> dict:
        reasons = {
            "Scout": "发现问题包含明确迷路焦虑，适合进入训练沙盒。",
            "Collect": "问题带有市场、平台和痛点字段，可以用于独立 JAG-LAB 训练。",
            "Analyze": "痛点强度和回复潜力达到训练阈值。",
            "Classify": "问题应归入交通焦虑、首次旅行和路线救援。",
            "Prioritize": f"Opportunity verdict={score['verdict']}，不是所有问题都会自动高价值。",
            "Strategy": "策略选择救援式回答，因为用户处于旅途中不确定状态。",
            "Generate": "回答生成遵循平台人格，Reddit 深度真实，TikTok 短 Hook，X 快速观点。",
            "Human Review": "任何回答、策略和学习结论必须先进入人工 Gate。",
            "Learn": "只学习被批准的方向，并记录错误学习被拒绝的原因。",
            "Deposit": "沉淀 Best Answer、Best Hook、Failed Strategy 等 Runtime Intelligence。",
        }
        return {
            "stage": stage,
            "question_id": question["question_id"],
            "why": reasons[stage],
            "score": score if stage in {"Analyze", "Prioritize"} else None,
            "platform_styles": style_plans if stage in {"Strategy", "Generate"} else None,
            "generated": generated if stage == "Generate" else None,
        }

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
