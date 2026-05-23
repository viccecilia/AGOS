from __future__ import annotations

import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.action_recommendation_engine import ActionRecommendationEngine


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "action_recommendations"
        report = ActionRecommendationEngine(root).recommend()

        assert report["report_id"] == "ACTION_RECOMMENDATION_REPORT"
        assert report["status"] == "recommendations_ready"
        assert report["scope"] == "local_human_gated_recommendations_only"
        assert len(report["actionRecommendations"]) >= 4
        action_types = {item["action_type"] for item in report["actionRecommendations"]}
        assert {"today_content", "today_reply", "today_platform", "today_trend"}.issubset(action_types)
        assert report["actionRecommendationFeed"], "action recommendation feed must exist"
        assert report["recommendationSummary"]["requires_human_review"] is True

        for item in report["actionRecommendations"]:
            assert item["why_recommended"], "recommendation must explain why"
            assert item["risk_level"], "recommendation must include risk level"
            assert item["expected_result"], "recommendation must include expected result"
            assert item["recommended_platform"], "recommendation must include platform"
            assert item["recommended_personality"], "recommendation must include personality"
            assert item["recommended_market"], "recommendation must include market"
            assert item["review_status"] == "needs_human_review"
            assert item["execution_boundary"] == "local recommendation only; no external action"

        assert (root / "ACTION_RECOMMENDATION_REPORT.json").exists()
        assert (root / "action_recommendations.json").exists()
        assert (root / "action_recommendation_feed.json").exists()

    print("action recommendation smoke test passed")


if __name__ == "__main__":
    main()
