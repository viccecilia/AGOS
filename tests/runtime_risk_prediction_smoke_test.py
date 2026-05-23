from __future__ import annotations

import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.runtime_risk_prediction import RuntimeRiskPrediction


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "runtime_risk"
        report = RuntimeRiskPrediction(root).predict()

        assert report["report_id"] == "RUNTIME_RISK_REPORT"
        assert report["status"] == "risk_predicted"
        assert report["scope"] == "local_runtime_risk_prediction_only"
        risk_types = {item["risk_type"] for item in report["runtimeRiskMatrix"]}
        assert {
            "spam risk",
            "platform risk",
            "drift risk",
            "over-marketing risk",
            "repetition risk",
        }.issubset(risk_types)
        assert report["runtimeRiskFeed"], "runtime risk feed is required"
        assert report["riskSummary"]["requires_human_review"] is True

        for item in report["runtimeRiskMatrix"]:
            assert item["level"] in {"low", "medium", "high"}
            assert item["reason"]
            assert item["mitigation"]

        assert (root / "RUNTIME_RISK_REPORT.json").exists()
        assert (root / "runtime_risk_feed.json").exists()
        assert (root / "runtime_risk_matrix.json").exists()

    print("runtime risk prediction smoke test passed")


if __name__ == "__main__":
    main()
