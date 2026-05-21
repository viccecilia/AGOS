"""Workspace-scoped growth report engine."""

from __future__ import annotations

import json
from pathlib import Path

from models.report import GrowthReport
from schemas.report_schema import validate_report_payload
from services.content_engine import ContentDraftStore
from services.learning_engine import LearningEventStore
from services.pain_point_engine import PainPointStore
from services.reply_engine import ReplyDraftStore
from services.workspace_service import WorkspaceStore


class ReportEngine:
    def __init__(self, workspace_store: WorkspaceStore | None = None) -> None:
        self.workspace_store = workspace_store or WorkspaceStore()
        self.pain_points = PainPointStore(self.workspace_store)
        self.content = ContentDraftStore(self.workspace_store)
        self.replies = ReplyDraftStore(self.workspace_store)
        self.learning = LearningEventStore(self.workspace_store)

    def generate(self, workspace_id: str, report_type: str) -> GrowthReport:
        self.workspace_store.get(workspace_id)
        pain_count = len(self.pain_points.list(workspace_id))
        content_count = len(self.content.list(workspace_id))
        reply_count = len(self.replies.list(workspace_id))
        recommendations = self.learning.recommendations(workspace_id)
        payload = {
            "report_id": f"{workspace_id}_{report_type}_report",
            "workspace_id": workspace_id,
            "report_type": report_type,
            "title": f"{report_type.title()} Growth Report",
            "summary": (
                f"Sample {report_type} report for {workspace_id}: "
                f"{pain_count} pain points, {content_count} content drafts, {reply_count} reply drafts, "
                f"{len(recommendations)} learning recommendations. Sample data only."
            ),
            "metrics": {
                "pain_points": pain_count,
                "content_drafts": content_count,
                "reply_drafts": reply_count,
                "learning_recommendations": len(recommendations),
            },
            "recommendations": [
                f"Prioritize {item['target_type']} {item['target_id']} with score {item['score']}"
                for item in recommendations[:3]
            ] or ["Collect more feedback before changing content priorities."],
        }
        return self.write(payload)

    def write(self, payload: dict) -> GrowthReport:
        validate_report_payload(payload)
        report = GrowthReport.from_dict(payload)
        path = self._report_file(report.workspace_id, report.report_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        return report

    def _report_file(self, workspace_id: str, report_id: str) -> Path:
        workspace_file = self.workspace_store._workspace_file(workspace_id)
        return workspace_file.parent / "reports" / f"{report_id}.json"
