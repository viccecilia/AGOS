"""Workspace-scoped learning loop service."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from models.learning import LearningEvent
from schemas.learning_schema import validate_learning_payload
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

    def _events_dir(self, workspace_id: str) -> Path:
        workspace_file = self.workspace_store._workspace_file(workspace_id)
        return workspace_file.parent / "learning_events"

    def _event_file(self, workspace_id: str, event_id: str) -> Path:
        return self._events_dir(workspace_id) / f"{event_id}.json"
