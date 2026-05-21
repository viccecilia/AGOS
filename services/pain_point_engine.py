"""Workspace-scoped pain point radar engine.

R005 uses local sample data only. It does not scrape websites or bypass platform
restrictions.
"""

from __future__ import annotations

import json
from pathlib import Path

from models.pain_point import PainPoint
from schemas.pain_point_schema import validate_pain_point_payload
from services.workspace_service import WorkspaceStore


class PainPointNotFoundError(KeyError):
    pass


class PainPointStore:
    def __init__(self, workspace_store: WorkspaceStore | None = None) -> None:
        self.workspace_store = workspace_store or WorkspaceStore()

    def import_many(self, workspace_id: str, payloads: list[dict]) -> list[PainPoint]:
        self.workspace_store.get(workspace_id)
        return [self.upsert({**payload, "workspace_id": workspace_id}) for payload in payloads]

    def upsert(self, payload: dict) -> PainPoint:
        validate_pain_point_payload(payload)
        workspace_id = str(payload["workspace_id"])
        self.workspace_store.get(workspace_id)
        pain_point = PainPoint.from_dict(payload)
        path = self._pain_point_file(workspace_id, pain_point.pain_point_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(pain_point.to_dict(), ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return pain_point

    def list(self, workspace_id: str, platform: str | None = None, category: str | None = None) -> list[PainPoint]:
        self.workspace_store.get(workspace_id)
        root = self._pain_points_dir(workspace_id)
        if not root.exists():
            return []
        items = [
            PainPoint.from_dict(json.loads(path.read_text(encoding="utf-8")))
            for path in root.glob("*.json")
        ]
        if platform:
            items = [item for item in items if item.platform == platform]
        if category:
            items = [item for item in items if item.category == category]
        return sorted(items, key=lambda item: item.pain_point_id)

    def top(self, workspace_id: str, limit: int = 5) -> list[PainPoint]:
        return sorted(self.list(workspace_id), key=lambda item: item.priority_score, reverse=True)[:limit]

    def _pain_points_dir(self, workspace_id: str) -> Path:
        workspace_file = self.workspace_store._workspace_file(workspace_id)
        return workspace_file.parent / "pain_points"

    def _pain_point_file(self, workspace_id: str, pain_point_id: str) -> Path:
        validate_pain_point_payload(
            {
                "workspace_id": workspace_id,
                "pain_point_id": pain_point_id,
                "source": "placeholder",
                "platform": "seo",
                "market": "placeholder",
                "audience": "placeholder",
                "category": "placeholder",
                "title": "placeholder",
                "evidence": "placeholder",
                "trend_score": 0,
                "urgency_score": 0,
                "value_score": 0,
                "tags": [],
            }
        )
        return self._pain_points_dir(workspace_id) / f"{pain_point_id}.json"
