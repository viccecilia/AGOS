from __future__ import annotations

import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.learning_engine import LearningEventStore
from services.report_engine import ReportEngine
from services.workspace_service import WorkspaceStore


def main() -> None:
    root = Path("runtime/test_report_workspaces")
    if root.exists():
        shutil.rmtree(root)

    workspace_store = WorkspaceStore(root)
    workspace_store.create({"workspace_id": "alpha_japan", "name": "Alpha", "owner": "Alpha Co", "product_name": "Guide", "industry": "travel"})
    learning = LearningEventStore(workspace_store)
    learning.record({"event_id": "ev1", "workspace_id": "alpha_japan", "target_type": "content_draft", "target_id": "draft_a", "signal": "converted", "weight": 50})

    engine = ReportEngine(workspace_store)
    reports = [engine.generate("alpha_japan", kind) for kind in ["daily", "weekly", "monthly"]]
    assert {report.report_type for report in reports} == {"daily", "weekly", "monthly"}
    assert all("Sample" in report.summary for report in reports)
    assert reports[0].metrics["learning_recommendations"] == 1
    assert "draft_a" in reports[0].recommendations[0]

    shutil.rmtree(root)
    print("report smoke test passed")


if __name__ == "__main__":
    main()
