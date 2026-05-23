from __future__ import annotations

import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.semi_autonomous_runtime_gate import SemiAutonomousRuntimeGate


def main() -> None:
    action = {
        "status": "recommendations_ready",
        "actionRecommendations": [
            {"action_id": "REC-CONTENT-001"},
            {"action_id": "REC-REPLY-001"},
            {"action_id": "REC-PLATFORM-001"},
            {"action_id": "REC-TREND-001"},
        ],
    }
    plan = {
        "status": "ready_for_human_review",
        "todayOperationPlan": [
            {"plan_id": "PLAN-0001"},
            {"plan_id": "PLAN-0002"},
            {"plan_id": "PLAN-0003"},
            {"plan_id": "PLAN-0004"},
        ],
        "runtimePlanSummary": {"pending_approval": 4},
    }
    approval = {
        "status": "active",
        "approvalSummary": {
            "total_items": 4,
            "action_queue_items": 4,
            "review_queue_items": 0,
            "correction_queue_items": 0,
        },
    }
    risk = {
        "status": "risk_predicted",
        "riskSummary": {"overall_risk": "medium"},
        "runtimeRiskMatrix": [
            {"risk_type": "spam risk"},
            {"risk_type": "platform risk"},
            {"risk_type": "drift risk"},
            {"risk_type": "over-marketing risk"},
            {"risk_type": "repetition risk"},
        ],
    }
    simulation = {
        "status": "simulated",
        "executionSimulationSummary": {
            "total_scenarios": 4,
            "external_execution_enabled": False,
        },
        "executionSimulationScenarios": [
            {"external_execution": False},
            {"external_execution": False},
            {"external_execution": False},
            {"external_execution": False},
        ],
    }
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "semi_auto_gate"
        report = SemiAutonomousRuntimeGate(root).evaluate(action, plan, approval, risk, simulation)

        assert report["report_id"] == "SEMI_AUTONOMOUS_RUNTIME_REPORT"
        assert report["status"] == "passed"
        assert report["semiAutonomousRuntimeCapability"]["can_recommend_actions"] is True
        assert report["semiAutonomousRuntimeCapability"]["can_plan_runtime"] is True
        assert report["semiAutonomousRuntimeCapability"]["can_unify_human_approval"] is True
        assert report["semiAutonomousRuntimeCapability"]["can_predict_risk"] is True
        assert report["semiAutonomousRuntimeCapability"]["can_simulate_execution"] is True
        assert report["semiAutonomousRuntimeCapability"]["external_execution_enabled"] is False
        assert report["semiAutonomousRuntimeCapability"]["ready_for_controlled_external_operations_preparation"] is True
        assert report["semiAutonomousRuntimeSummary"]["next_stage"] == "Controlled External Operations Preparation Stage"
        assert len(report["checks"]) == 6
        assert all(item["status"] == "passed" for item in report["checks"])
        assert report["runtimeIntelligenceGateReview"]["evidence"]["simulation_scenarios"] == 4

        assert (root / "SEMI_AUTONOMOUS_RUNTIME_REPORT.json").exists()
        assert (root / "RUNTIME_INTELLIGENCE_GATE_REVIEW.json").exists()
        assert (root / "semi_autonomous_runtime_checks.json").exists()

    print("semi autonomous runtime gate smoke test passed")


if __name__ == "__main__":
    main()
