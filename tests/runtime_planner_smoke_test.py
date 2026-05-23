from __future__ import annotations

import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.runtime_planner import RuntimePlanner


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "runtime_plans"
        report = RuntimePlanner(root).plan()

        assert report["report_id"] == "RUNTIME_ACTION_PLAN"
        assert report["scope"] == "local_runtime_plan_only"
        assert report["todayOperationPlan"], "runtime plan items must exist"
        assert report["todayPlatformFocus"]["primary_platform"], "platform focus is required"
        assert report["todayContentRhythm"]["rhythm"], "content rhythm is required"
        assert report["todayReplyPriority"]["priority"], "reply priority is required"
        assert report["runtimePlanFeed"], "runtime plan feed is required"

        for item in report["todayOperationPlan"]:
            assert item["planned_action"]
            assert item["platform"]
            assert item["time_block"]
            assert item["why_this_plan"]
            assert item["execution_boundary"] == "local plan only; no external action"

        assert (root / "RUNTIME_ACTION_PLAN.json").exists()
        assert (root / "runtime_plan.json").exists()
        assert (root / "runtime_plan_feed.json").exists()

    print("runtime planner smoke test passed")


if __name__ == "__main__":
    main()
