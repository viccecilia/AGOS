from __future__ import annotations

import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.action_queue_engine import ActionQueueEngine


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "action_queue"
        engine = ActionQueueEngine(root)
        report = engine.build_queue()

        assert report["report_id"] == "ACTION_QUEUE_REPORT"
        assert report["status"] == "active"
        assert report["scope"] == "local_human_gated_action_queue_only"
        assert len(report["actionQueue"]) >= 4
        assert report["actionQueueSummary"]["needs_human_approval"] == len(report["actionQueue"])
        assert report["actionQueueFeed"], "action queue feed must exist"

        for item in report["actionQueue"]:
            assert item["status"] == "needs_human_approval"
            assert item["why_recommended"]
            assert item["risk_level"]
            assert item["execution_boundary"] == "local approval queue only; no external action"

        ids = [item["action_id"] for item in report["actionQueue"]]
        engine.approve(ids[0], "Approved for local planning.")
        engine.reject(ids[1], "Too risky for today.")
        engine.modify(ids[2], "Prioritize Reddit but reduce frequency.", "Narrow the action.")
        engine.postpone(ids[3], "Wait for more evidence.")
        updated = engine.state()

        statuses = {item["action_id"]: item["status"] for item in updated["actionQueue"]}
        assert statuses[ids[0]] == "approved"
        assert statuses[ids[1]] == "rejected"
        assert statuses[ids[2]] == "modified"
        assert statuses[ids[3]] == "postponed"
        assert updated["actionQueueSummary"]["decisions_recorded"] == 4
        assert len(updated["humanActionDecisions"]) == 4

        assert (root / "ACTION_QUEUE_REPORT.json").exists()
        assert (root / "action_queue.json").exists()
        assert (root / "human_action_decisions.json").exists()

    print("action queue smoke test passed")


if __name__ == "__main__":
    main()
