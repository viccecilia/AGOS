from __future__ import annotations

import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.runtime_execution_simulator import RuntimeExecutionSimulator


def main() -> None:
    runtime_plan = {
        "todayOperationPlan": [
            {
                "action_id": "ACT-CONTENT-001",
                "action_type": "today_content",
                "planned_action": "Prepare a Tokyo transport guide post.",
                "platform": "Reddit",
                "market": "Japan",
                "personality": "trusted_guide",
                "approval_state": "needs_human_approval",
            },
            {
                "action_id": "ACT-REPLY-001",
                "action_type": "today_reply",
                "planned_action": "Prepare two answer drafts.",
                "platform": "Reddit",
                "market": "Japan",
                "personality": "trusted_guide",
                "approval_state": "approved",
            },
            {
                "action_id": "ACT-TREND-001",
                "action_type": "today_trend",
                "planned_action": "Simulate cross-platform trend expansion.",
                "platform": "TikTok",
                "market": "Japan",
                "personality": "hook_short",
                "approval_state": "needs_human_approval",
            },
            {
                "action_id": "ACT-PLATFORM-001",
                "action_type": "today_platform",
                "planned_action": "Prioritize Reddit today.",
                "platform": "Reddit",
                "market": "Japan",
                "personality": "trusted_guide",
                "approval_state": "modified",
            },
        ]
    }
    approval = {
        "unifiedApprovalQueue": [
            {"queue_type": "action", "target_id": "ACT-CONTENT-001", "status": "needs_human_approval"},
            {"queue_type": "action", "target_id": "ACT-REPLY-001", "status": "approved"},
            {"queue_type": "action", "target_id": "ACT-TREND-001", "status": "needs_human_approval"},
            {"queue_type": "action", "target_id": "ACT-PLATFORM-001", "status": "modified"},
        ]
    }
    risk = {"riskSummary": {"overall_risk": "medium", "highest_risk": "repetition risk"}}

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "execution_simulation"
        report = RuntimeExecutionSimulator(root).simulate(runtime_plan, approval, risk)

        assert report["report_id"] == "EXECUTION_SIMULATION_REPORT"
        assert report["scope"] == "local_safe_runtime_execution_simulation_only"
        assert report["status"] == "simulated"
        assert report["executionSimulationSummary"]["total_scenarios"] == 4
        assert report["executionSimulationSummary"]["content_publish"] == 1
        assert report["executionSimulationSummary"]["reply_action"] == 1
        assert report["executionSimulationSummary"]["diffusion_action"] == 1
        assert report["executionSimulationSummary"]["platform_operation"] == 1
        assert report["executionSimulationSummary"]["blocked_by_human_gate"] == 2
        assert report["executionSimulationSummary"]["ready_for_local_dry_run"] == 2
        assert report["executionSimulationSummary"]["external_execution_enabled"] is False
        assert report["executionSimulationFeed"]

        for item in report["executionSimulationScenarios"]:
            assert item["what_would_happen"]
            assert item["expected_positive_signal"]
            assert item["expected_negative_signal"]
            assert item["external_execution"] is False
            assert item["execution_boundary"] == "simulation only; no external action"

        assert (root / "EXECUTION_SIMULATION_REPORT.json").exists()
        assert (root / "execution_simulation_scenarios.json").exists()
        assert (root / "execution_simulation_feed.json").exists()

    print("runtime execution simulation smoke test passed")


if __name__ == "__main__":
    main()
