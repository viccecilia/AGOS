from __future__ import annotations

import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.controlled_api_collection_gate import ControlledAPICollectionGate


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        gate = ControlledAPICollectionGate(Path(tmp) / "controlled_api_collection_gate")
        report = gate.evaluate("JAG-LAB")
        summary = report["controlledAPICollectionSummary"]
        safety_review = report["platformIntelligenceSafetyReview"]

        assert report["report_id"] == "CONTROLLED_API_COLLECTION_REPORT"
        assert report["status"] == "passed"
        assert report["phase"] == "CONTROLLED_API_INTELLIGENCE_COLLECTION"
        assert report["gate"] == "Controlled API Collection Gate"
        assert set(report["validatedCapabilities"]) == {
            "Platform Connection Center",
            "Credential Vault",
            "Live Collection Runner",
            "Compliance Guard",
            "Normalization Pipeline",
            "Live Memory Import",
            "Collection Review & Correction",
        }

        checks = report["controlledAPICollectionChecks"]
        assert len(checks) == 7
        assert all(item["status"] == "passed" for item in checks)
        assert summary["checks"] == 7
        assert summary["passed"] == 7
        assert summary["needs_review"] == 0
        assert summary["safe_batch_platform_intelligence_ready"] is True
        assert summary["controlled_api_intelligence_collection_complete"] is True
        assert summary["ready_for_next_phase"] is True
        assert summary["next_phase"] == "Controlled Real External Interaction Stage"
        assert summary["write_operations_enabled"] is False
        assert summary["automatic_login_scraping_enabled"] is False
        assert summary["automatic_external_interaction_enabled"] is False

        assert safety_review["review_id"] == "PLATFORM_INTELLIGENCE_SAFETY_REVIEW"
        assert safety_review["blocking_risk"] is False
        assert safety_review["overall_risk"] == "controlled"
        assert len(safety_review["riskItems"]) >= 5
        assert safety_review["phaseExitRecommendation"] == "pass_to_controlled_real_external_interaction_stage"

        root = Path(tmp) / "controlled_api_collection_gate"
        assert (root / "CONTROLLED_API_COLLECTION_REPORT.json").exists()
        assert (root / "PLATFORM_INTELLIGENCE_SAFETY_REVIEW.json").exists()
        assert (root / "controlled_api_collection_checks.json").exists()
        assert (root / "controlled_api_collection_summary.json").exists()

    print("controlled_api_collection_gate_smoke_test passed")


if __name__ == "__main__":
    main()
