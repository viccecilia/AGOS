from __future__ import annotations

import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.autonomous_growth_preparation_gate import AutonomousGrowthPreparationGate


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "autonomous_growth_preparation_gate"
        report = AutonomousGrowthPreparationGate(root).evaluate()

        assert report["report_id"] == "AUTONOMOUS_GROWTH_PREPARATION_REPORT"
        assert report["status"] == "passed"
        assert report["phase"] == "AUTONOMOUS_GROWTH_PREPARATION"

        checks = {item["name"]: item for item in report["checks"]}
        required = {
            "Runtime Intelligence",
            "Personality Intelligence",
            "Scout Intelligence",
            "Real Ops Intelligence",
            "Strategy Intelligence",
        }
        assert required.issubset(checks)
        assert all(checks[name]["status"] == "passed" for name in required)

        capability = report["autonomousGrowthPreparationCapability"]
        assert capability["ready_for_semi_autonomous_runtime"] is True
        assert capability["human_gate_required"] is True

        summary = report["autonomousGrowthPreparationSummary"]
        assert summary["phase_completion"] == "Autonomous Growth Preparation Phase completed"
        assert summary["next_stage"] == "Semi-Autonomous Runtime Stage"
        assert summary["gate_decision"] == "pass_to_semi_autonomous_runtime"

        review = report["runtimeIntelligenceReview"]
        assert review["next_stage"] == "Semi-Autonomous Runtime Stage"
        assert review["human_gate_required"] is True
        assert "No autonomous posting" in review["safety_boundary"]

        assert (root / "AUTONOMOUS_GROWTH_PREPARATION_REPORT.json").exists()
        assert (root / "RUNTIME_INTELLIGENCE_REVIEW.json").exists()
        assert (root / "autonomous_growth_preparation_checks.json").exists()

    print("autonomous growth preparation gate smoke test passed")


if __name__ == "__main__":
    main()
