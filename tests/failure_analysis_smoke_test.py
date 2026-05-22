import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.failure_analysis_engine import FailureAnalysisEngine


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "failure_analysis"
        report = FailureAnalysisEngine(root).analyze()

        assert report["report_id"] == "FAILURE_ANALYSIS_REPORT"
        assert report["status"] == "active"
        assert report["scope"] == "local_failure_analysis_only_no_platform_api"
        assert report["failureItems"], "failure items must be generated"
        assert report["failureTimeline"], "failure timeline must be generated"
        assert report["failureSummary"]["can_explain_failure"] is True
        assert report["failureSummary"]["ignored_replies"] >= 1
        assert report["failureSummary"]["failed_hooks"] >= 1
        assert report["failureSummary"]["failed_strategies"] >= 1

        for item in report["failureItems"]:
            assert item.get("why_failed"), "each failure item must explain why it failed"
            assert item.get("fix_recommendation"), "each failure item must recommend a fix"

        assert (root / "FAILURE_ANALYSIS_REPORT.json").exists()
        assert (root / "failure_items.json").exists()
        assert (root / "failure_timeline.json").exists()
    print("failure analysis smoke test passed")


if __name__ == "__main__":
    main()
