from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.personality_review_session import PersonalityReviewSession


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "personality_reviews"
        session = PersonalityReviewSession(root)
        report = session.generate(window_hours=24)

        assert report["report_id"] == "PERSONALITY_REVIEW_SESSION_REPORT"
        assert report["window_hours"] == 24
        assert "recentDrift" in report
        assert "recentBestPersonality" in report
        assert "recentFailedTone" in report
        assert "personalityTrend" in report
        assert len(report["personalityTrend"]) == 3

        trend_by_signal = {item["signal"]: item for item in report["personalityTrend"]}
        assert {"approved_personality", "failed_tone", "personality_drift"}.issubset(trend_by_signal)
        assert trend_by_signal["approved_personality"]["summary"]
        assert report["reviewSummary"]
        assert session.report_path.exists()
        assert session.history_path.exists()

        saved = json.loads(session.report_path.read_text(encoding="utf-8"))
        history = json.loads(session.history_path.read_text(encoding="utf-8"))
        assert saved["report_id"] == report["report_id"]
        assert history[-1]["report_id"] == report["report_id"]

    print("personality review session smoke test passed")


if __name__ == "__main__":
    main()
