"""Workspace-scoped learning loop service."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from models.learning import LearningEvent
from schemas.learning_schema import validate_learning_payload
from services.answer_branch_engine import AnswerBranchStore
from services.reply_attempt_engine import ReplyAttemptStore
from services.workspace_service import WorkspaceStore


class LearningEventStore:
    def __init__(self, workspace_store: WorkspaceStore | None = None) -> None:
        self.workspace_store = workspace_store or WorkspaceStore()

    def record(self, payload: dict) -> LearningEvent:
        validate_learning_payload(payload)
        self.workspace_store.get(str(payload["workspace_id"]))
        event = LearningEvent.from_dict(payload)
        path = self._event_file(event.workspace_id, event.event_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(event.to_dict(), ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        return event

    def list(self, workspace_id: str) -> list[LearningEvent]:
        self.workspace_store.get(workspace_id)
        root = self._events_dir(workspace_id)
        if not root.exists():
            return []
        return sorted(
            [LearningEvent.from_dict(json.loads(path.read_text(encoding="utf-8"))) for path in root.glob("*.json")],
            key=lambda item: item.event_id,
        )

    def recommendations(self, workspace_id: str) -> list[dict]:
        scores: dict[tuple[str, str], float] = defaultdict(float)
        signals: dict[tuple[str, str], list[str]] = defaultdict(list)
        for event in self.list(workspace_id):
            key = (event.target_type, event.target_id)
            scores[key] += event.weight
            signals[key].append(event.signal)
        return [
            {"target_type": key[0], "target_id": key[1], "score": round(score, 4), "signals": signals[key]}
            for key, score in sorted(scores.items(), key=lambda item: item[1], reverse=True)
        ]

    def ingest_reply_attempt(
        self,
        workspace_id: str,
        reply_attempt_id: str,
        reply_attempt_store: ReplyAttemptStore | None = None,
    ) -> list[LearningEvent]:
        attempts = reply_attempt_store or ReplyAttemptStore(self.workspace_store)
        attempt = attempts.get(workspace_id, reply_attempt_id)
        events: list[LearningEvent] = []
        signal_weights = {
            "liked": attempt.liked * 10,
            "positive_reply": attempt.replied * 20,
            "ignored": attempt.ignored * -15,
            "saved": attempt.saved * 25,
            "shared": attempt.shared * 30,
        }
        if attempt.status in {"posted", "high_engagement"}:
            signal_weights["attempt_posted"] = 5
        for signal, weight in signal_weights.items():
            if weight == 0:
                continue
            event_id = f"{attempt.reply_attempt_id}_{signal}"
            events.append(
                self.record(
                    {
                        "event_id": event_id,
                        "workspace_id": workspace_id,
                        "target_type": "answer_branch",
                        "target_id": attempt.branch_id,
                        "signal": signal,
                        "weight": weight,
                        "metadata": {
                            "reply_attempt_id": attempt.reply_attempt_id,
                            "question_id": attempt.question_id,
                            "platform": attempt.platform,
                        },
                    }
                )
            )
        return events

    def best_answer_branches(self, workspace_id: str) -> list[dict]:
        return [item for item in self.recommendations(workspace_id) if item["target_type"] == "answer_branch"]

    def update_best_answer_branch(
        self,
        workspace_id: str,
        answer_branch_store: AnswerBranchStore | None = None,
    ) -> dict | None:
        branches = self.best_answer_branches(workspace_id)
        if not branches:
            return None
        store = answer_branch_store or AnswerBranchStore(self.workspace_store)
        best = branches[0]
        store.mark_best(workspace_id, best["target_id"])
        return best

    def _events_dir(self, workspace_id: str) -> Path:
        workspace_file = self.workspace_store._workspace_file(workspace_id)
        return workspace_file.parent / "learning_events"

    def _event_file(self, workspace_id: str, event_id: str) -> Path:
        return self._events_dir(workspace_id) / f"{event_id}.json"
