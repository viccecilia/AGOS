"""Runtime pipeline state machine for the local AGOS Runtime OS."""

from __future__ import annotations

from dataclasses import dataclass, field


PIPELINE = [
    "Scout",
    "Collect",
    "Analyze",
    "Classify",
    "Prioritize",
    "Strategy",
    "Generate",
    "Human Review",
    "Learn",
    "Deposit",
]

TERMINAL_STAGE_STATUS = {"done", "failed", "paused", "waiting_review", "pending"}


class RuntimeStateMachineError(ValueError):
    pass


@dataclass
class RuntimeStateMachine:
    current_stage: str = "Scout"
    stage_status: dict[str, str] = field(default_factory=dict)
    error: str | None = None

    def __post_init__(self) -> None:
        if self.current_stage not in PIPELINE:
            raise RuntimeStateMachineError(f"Unknown runtime stage: {self.current_stage}")
        for stage in PIPELINE:
            self.stage_status.setdefault(stage, "waiting")
        self.stage_status[self.current_stage] = "current"

    @property
    def next_stage(self) -> str | None:
        index = PIPELINE.index(self.current_stage)
        if index >= len(PIPELINE) - 1:
            return None
        return PIPELINE[index + 1]

    def complete_current(self) -> str:
        if self.current_stage == "Human Review":
            raise RuntimeStateMachineError("Human Review requires approve/reject/modify")
        next_stage = self.next_stage
        self.stage_status[self.current_stage] = "done"
        if next_stage is None:
            return self.current_stage
        self.current_stage = next_stage
        self.stage_status[self.current_stage] = "current"
        if self.current_stage == "Human Review":
            self.stage_status[self.current_stage] = "waiting_review"
        return self.current_stage

    def fail_current(self, error: str) -> None:
        self.error = error
        self.stage_status[self.current_stage] = "failed"

    def pause_current(self) -> None:
        self.stage_status[self.current_stage] = "paused"

    def resume_current(self) -> None:
        if self.stage_status.get(self.current_stage) == "paused":
            self.stage_status[self.current_stage] = "current"

    def approve_human_gate(self) -> str:
        if self.current_stage != "Human Review":
            raise RuntimeStateMachineError("Approve is only valid at Human Review")
        self.stage_status[self.current_stage] = "done"
        self.current_stage = "Learn"
        self.stage_status[self.current_stage] = "current"
        return self.current_stage

    def reject_human_gate(self, reason: str) -> None:
        if self.current_stage != "Human Review":
            raise RuntimeStateMachineError("Reject is only valid at Human Review")
        self.error = reason
        self.stage_status[self.current_stage] = "failed"

    def modify_human_gate(self, note: str) -> None:
        if self.current_stage != "Human Review":
            raise RuntimeStateMachineError("Modify is only valid at Human Review")
        self.error = note
        self.stage_status[self.current_stage] = "waiting_review"

    def to_pipeline(self) -> list[dict]:
        return [
            {
                "id": stage,
                "label": stage,
                "status": self.stage_status.get(stage, "waiting"),
                "note": self._stage_note(stage),
            }
            for stage in PIPELINE
        ]

    @classmethod
    def from_pipeline(cls, current_stage: str, pipeline: list[dict] | None = None) -> "RuntimeStateMachine":
        statuses = {item["id"]: item.get("status", "waiting") for item in pipeline or [] if item.get("id") in PIPELINE}
        return cls(current_stage=current_stage, stage_status=statuses)

    @staticmethod
    def _stage_note(stage: str) -> str:
        notes = {
            "Scout": "发现候选问题",
            "Collect": "收集问题与来源",
            "Analyze": "分析痛点和情绪",
            "Classify": "分类到库",
            "Prioritize": "排序高价值机会",
            "Strategy": "生成策略",
            "Generate": "生成回复/内容",
            "Human Review": "等待人工 Gate",
            "Learn": "学习反馈",
            "Deposit": "沉淀记忆",
        }
        return notes[stage]
