import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.real_growth_validation_engine import RealGrowthValidationEngine


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "real_growth_validation"
        report = RealGrowthValidationEngine(root).validate()

        assert report["report_id"] == "REAL_GROWTH_VALIDATION_REPORT"
        assert report["status"] == "passed"
        assert report["scope"] == "local_real_operations_validation"

        checks = {item["name"]: item for item in report["validationChecks"]}
        required = {
            "runtime_stable",
            "scout_effective",
            "reply_effective",
            "feedback_effective",
            "learning_effective",
            "workspace_growth_supported",
        }
        assert required.issubset(checks), "all Real Growth validation checks must exist"
        assert all(checks[name]["status"] == "passed" for name in required)

        summary = report["realGrowthValidationSummary"]
        assert summary["growth_intelligence"] == "formed"
        assert summary["phase_completion"] == "Real Operations Phase completed"
        assert summary["next_stage"] == "Autonomous Growth Preparation Stage"
        assert report["runtimeIntelligenceReview"]["next_stage"] == "Autonomous Growth Preparation Stage"

        assert (root / "REAL_GROWTH_VALIDATION_REPORT.json").exists()
        assert (root / "RUNTIME_INTELLIGENCE_REVIEW.json").exists()
    print("real growth validation smoke test passed")


if __name__ == "__main__":
    main()
