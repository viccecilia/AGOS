"""Manual prospect discovery importer.

This service intentionally supports only manual text, JSON, and CSV-style
payloads. It does not scrape platforms, register accounts, or bypass platform
limits.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable

from services.question_inbox_engine import QuestionInboxStore
from services.workspace_service import WorkspaceStore


EMOTION_KEYWORDS = {
    "confused": ["confused", "lost", "unclear", "헷갈", "不清楚", "不知道"],
    "urgent": ["urgent", "asap", "today", "急", "趕", "빨리"],
    "frustrated": ["frustrated", "annoying", "tired", "累", "困擾", "답답"],
}


class ProspectDiscoveryEngine:
    def __init__(
        self,
        workspace_store: WorkspaceStore | None = None,
        question_store: QuestionInboxStore | None = None,
    ) -> None:
        self.workspace_store = workspace_store or WorkspaceStore()
        self.question_store = question_store or QuestionInboxStore(self.workspace_store)

    def import_questions(self, workspace_id: str, questions: Iterable[dict]) -> list:
        self.workspace_store.get(workspace_id)
        imported = []
        for raw in questions:
            payload = {**raw, "workspace_id": workspace_id}
            text = str(payload.get("question_text", ""))
            payload.setdefault("emotion_tags", self.classify_emotions(text))
            payload.setdefault("priority_score", self.score_question(text, payload.get("emotion_tags", [])))
            payload.setdefault("status", "new")
            imported.append(self.question_store.upsert(payload))
        return imported

    def import_json_file(self, workspace_id: str, path: str | Path) -> list:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            payload = payload.get("questions", [])
        return self.import_questions(workspace_id, payload)

    def import_csv_file(self, workspace_id: str, path: str | Path) -> list:
        with Path(path).open("r", encoding="utf-8", newline="") as handle:
            return self.import_questions(workspace_id, csv.DictReader(handle))

    @staticmethod
    def classify_emotions(text: str) -> list[str]:
        lower = text.lower()
        tags = [tag for tag, keywords in EMOTION_KEYWORDS.items() if any(keyword.lower() in lower for keyword in keywords)]
        return tags or ["neutral"]

    @staticmethod
    def score_question(text: str, emotion_tags: list[str]) -> float:
        score = min(60 + len(text) / 12, 85)
        if "urgent" in emotion_tags:
            score += 10
        if "frustrated" in emotion_tags:
            score += 5
        return round(min(score, 100), 4)
