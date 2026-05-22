from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.heat_detection_engine import HeatDetectionEngine


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "heat_signals"
        report = HeatDetectionEngine(root).detect()

        assert report["report_id"] == "HEAT_DETECTION_REPORT"
        assert report["status"] == "active"
        assert report["scope"] == "local_only_no_external_platform_access"
        assert set(report["heatDimensions"]) == {
            "rising_trend",
            "high_engagement_trend",
            "high_emotion_trend",
            "high_spread_trend",
        }
        assert (root / "HEAT_DETECTION_REPORT.json").exists()
        assert (root / "heat_signals.json").exists()
        assert (root / "opportunity_ranking.json").exists()

        signals = report["heatSignals"]
        ranking = report["opportunityRanking"]
        assert signals
        assert ranking
        assert ranking[0]["rank"] == 1
        assert ranking[0]["opportunity_score"] >= ranking[-1]["opportunity_score"]
        assert any("rising_trend" in signal["detectedSignals"] for signal in signals)
        assert any("high_emotion_trend" in signal["detectedSignals"] for signal in signals)
        assert any("high_spread_trend" in signal["detectedSignals"] for signal in signals)
        assert any(signal["heat_level"] in {"hot", "warming"} for signal in signals)

        top_names = {item["cluster_name"] for item in ranking[:2]}
        assert "Tokyo transport anxiety" in top_names or "Tokyo rainy day travel friction" in top_names

        saved = json.loads((root / "HEAT_DETECTION_REPORT.json").read_text(encoding="utf-8"))
        assert saved["heatSummary"]["top_opportunity"] == ranking[0]["cluster_name"]

    print("heat detection smoke test passed")


if __name__ == "__main__":
    main()
