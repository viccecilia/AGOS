from __future__ import annotations

import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.growth_signal_correlation_engine import GrowthSignalCorrelationEngine


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "signal_correlation"
        report = GrowthSignalCorrelationEngine(root).correlate()

        assert report["report_id"] == "GROWTH_SIGNAL_CORRELATION_REPORT"
        assert report["status"] == "correlating_growth_signals"
        assert report["scope"] == "local_signal_correlation_only"
        matrix = report["signalCorrelationMatrix"]
        assert matrix["content_to_feedback"], "content to feedback correlations must exist"
        assert matrix["platform_to_growth"], "platform to growth correlations must exist"
        assert matrix["hook_to_interaction"], "hook to interaction correlations must exist"
        assert matrix["personality_to_result"], "personality to result correlations must exist"
        assert report["growthSignalCorrelationFeed"], "correlation feed must exist"
        assert report["correlationSummary"]["can_explain_growth_behavior"] is True

        for item in report["growthSignalCorrelationFeed"]:
            assert item["why_it_matters"], "each correlation feed item must explain why it matters"
            assert item["ai_action"], "each correlation feed item must include AI action"

        assert (root / "GROWTH_SIGNAL_CORRELATION_REPORT.json").exists()
        assert (root / "signal_correlation_matrix.json").exists()
        assert (root / "growth_signal_correlation_feed.json").exists()

    print("growth signal correlation smoke test passed")


if __name__ == "__main__":
    main()
