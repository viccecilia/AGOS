from __future__ import annotations

import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.api_scout_gate import APIScoutGate


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "api_scout_gate"
        report = APIScoutGate(root).evaluate()

        assert report["report_id"] == "API_SCOUT_VALIDATION_REPORT"
        assert report["status"] == "passed"
        assert report["phase"] == "PLATFORM_API_SCOUT_INTEGRATION"
        assert report["apiScoutGateSummary"]["checks"] == 6
        assert report["apiScoutGateSummary"]["passed"] == 6
        assert report["apiScoutGateSummary"]["safe_trend_intelligence_ready"] is True
        assert report["apiScoutGateSummary"]["ready_for_next_phase"] is True
        assert report["apiScoutGateSummary"]["write_operations_enabled"] is False

        capabilities = {item["capability"] for item in report["apiScoutGateChecks"]}
        assert {
            "API Registry",
            "Credential Vault",
            "Trend Connector",
            "API Safety Guard",
            "Signal Normalization",
            "API Scout Pipeline",
        }.issubset(capabilities)

        for check in report["apiScoutGateChecks"]:
            assert check["status"] == "passed"
            assert check["evidence"]
            assert check["result"]

        risk_review = report["platformApiRiskReview"]
        assert risk_review["review_id"] == "PLATFORM_API_RISK_REVIEW"
        assert risk_review["blocking_risk"] is False
        assert risk_review["phaseExitRecommendation"] == "pass_to_controlled_external_operations_preparation"
        assert len(risk_review["riskItems"]) >= 5
        risk_names = {item["risk"] for item in risk_review["riskItems"]}
        assert "write-side automation" in risk_names
        assert "credential leakage" in risk_names
        assert "platform rate-limit pressure" in risk_names

        assert (root / "API_SCOUT_VALIDATION_REPORT.json").exists()
        assert (root / "PLATFORM_API_RISK_REVIEW.json").exists()
        assert (root / "api_scout_gate_checks.json").exists()

    print("api scout gate smoke test passed")


if __name__ == "__main__":
    main()
