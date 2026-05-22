from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.strategic_interpretation_engine import StrategicInterpretationEngine


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "strategic_interpretation"
        report = StrategicInterpretationEngine(root).interpret()

        assert report["report_id"] == "STRATEGIC_INTERPRETATION_REPORT"
        assert report["status"] == "active"
        assert report["scope"] == "local_only_no_external_platform_access"
        assert set(report["interpretationDimensions"]) == {
            "why_trend_matters",
            "risk",
            "opportunity",
            "content_direction",
            "reply_direction",
            "platform_direction",
        }
        assert (root / "STRATEGIC_INTERPRETATION_REPORT.json").exists()
        assert (root / "strategic_interpretations.json").exists()
        assert (root / "strategic_feed.json").exists()

        interpretations = report["strategicInterpretations"]
        feed = report["strategicFeed"]
        assert interpretations
        assert feed
        assert len(feed) == len(interpretations)
        assert any(item["cluster_name"] == "Tokyo transport anxiety" for item in interpretations)
        assert all(item["why_trend_matters"] for item in interpretations)
        assert all(item["risk"]["items"] for item in interpretations)
        assert all(item["opportunity"]["summary"] for item in interpretations)
        assert all(item["content_direction"] for item in interpretations)
        assert all(item["reply_direction"] for item in interpretations)
        assert all(item["platform_direction"] for item in interpretations)
        assert any(item["review_required"] for item in interpretations)

        top = interpretations[0]
        assert top["heat_level"] in {"hot", "warming", "watch"}
        assert top["recommended_next_step"]
        saved = json.loads((root / "STRATEGIC_INTERPRETATION_REPORT.json").read_text(encoding="utf-8"))
        assert saved["strategicSummary"]["top_focus"] == top["cluster_name"]

    print("strategic interpretation smoke test passed")


if __name__ == "__main__":
    main()
