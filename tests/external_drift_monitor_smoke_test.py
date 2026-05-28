from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.external_drift_monitor import ExternalDriftMonitor
from services.promotion_feedback_learning import PromotionFeedbackLearning
from services.strategy_evolution_engine import StrategyEvolutionEngine


def main() -> None:
    strategy_state = StrategyEvolutionEngine().evaluate()
    feedback_learning = PromotionFeedbackLearning().learn()
    expected_actions = [
        {
            "simulation_id": "EXT-SIM-DRIFT-001",
            "external_action_id": "EXT-ACTION-DRIFT-001",
            "would_do": "Helpful Reddit answer with soft homepage reference.",
            "expected_result": "Human can review the suggested action and manually execute outside AGOS if approved.",
        },
        {
            "simulation_id": "EXT-SIM-DRIFT-002",
            "external_action_id": "EXT-ACTION-DRIFT-002",
            "would_do": "TikTok hook expected to produce saves.",
            "expected_result": "Expected useful saves and replies from target travelers.",
        },
    ]
    manual_feedback = [
        {
            "feedback_intake_id": "MANUAL-FEEDBACK-DRIFT-001",
            "platform": "Reddit",
            "views": 900,
            "likes": 1,
            "replies": 0,
            "saves": 0,
            "comments": ["This feels pushy"],
            "rejection_reason": "",
            "intake_status": "accepted_to_learning",
            "learning_memory_allowed": True,
        },
        {
            "feedback_intake_id": "MANUAL-FEEDBACK-DRIFT-002",
            "platform": "TikTok",
            "views": 0,
            "likes": 0,
            "replies": 0,
            "saves": 0,
            "comments": [],
            "rejection_reason": "Human rejected because the hook over-promised.",
            "intake_status": "rejected",
            "learning_memory_allowed": False,
        },
    ]

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "external_drift_monitor"
        report = ExternalDriftMonitor(root).monitor(
            expected_actions=expected_actions,
            manual_feedback=manual_feedback,
            strategy_state=strategy_state,
            feedback_learning=feedback_learning,
        )

        assert report["report_id"] == "EXTERNAL_DRIFT_REPORT"
        assert report["status"] == "external_drift_monitor_ready"
        signals = report["externalDriftSignals"]
        recommendations = report["externalDriftRecommendations"]
        summary = report["externalDriftSummary"]

        assert signals, "drift signals expected"
        assert recommendations, "drift recommendations expected"
        assert summary["external_drift_monitor_ready"] is True
        assert summary["recommendation_effectiveness_declining"] is True
        assert summary["strategy_drift_detected"] is True
        assert summary["platform_drift_detected"] is True
        assert summary["audience_drift_detected"] is True
        assert summary["tone_drift_detected"] is True
        assert summary["recommendation_only"] is True
        assert summary["auto_strategy_change_allowed"] is False
        assert summary["external_execution_change_allowed"] is False

        drift_types = {item["drift_type"] for item in signals}
        assert {"strategy_drift", "platform_drift", "audience_drift", "tone_drift"} <= drift_types

        for signal in signals:
            assert signal["recommendation_only"] is True
            assert signal["auto_strategy_change_allowed"] is False
            assert signal["external_execution_change_allowed"] is False
            assert "expected_result" in signal
            assert "actual_feedback_score" in signal

        for recommendation in recommendations:
            assert recommendation["recommendation_only"] is True
            assert recommendation["auto_strategy_change_allowed"] is False
            assert recommendation["external_execution_change_allowed"] is False

        for output_name in [
            "external_drift_signals.json",
            "external_drift_recommendations.json",
            "external_drift_summary.json",
            "EXTERNAL_DRIFT_REPORT.json",
        ]:
            path = root / output_name
            assert path.exists(), f"missing output: {output_name}"
            json.loads(path.read_text(encoding="utf-8"))

    print("external_drift_monitor_smoke_test passed")


if __name__ == "__main__":
    main()
