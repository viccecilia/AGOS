from __future__ import annotations

import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.synthetic_feedback_training import SYNTHETIC_TYPES, SyntheticFeedbackTraining


def main() -> None:
    replay_memory = [
        {
            "replay_id": "REPLAY-001",
            "topic": "Tokyo transport anxiety",
            "source_type": "historical_question",
            "replay_result": "question_priority_retrained",
        },
        {
            "replay_id": "REPLAY-002",
            "topic": "JR Pass decision pressure",
            "source_type": "historical_feedback",
            "replay_result": "engagement_pattern_reinforced",
        },
        {
            "replay_id": "REPLAY-003",
            "topic": "Over-marketing reply",
            "source_type": "historical_failure",
            "replay_result": "risk_pattern_reinforced",
        },
    ]
    with tempfile.TemporaryDirectory() as tmp:
        report = SyntheticFeedbackTraining(Path(tmp) / "synthetic_training").generate(replay_memory)
        dataset = report["syntheticTrainingDataset"]
        summary = report["syntheticTrainingSummary"]
        types = {item["synthetic_type"] for item in dataset}
        risks = {item["simulated_risk"] for item in dataset}

        assert report["status"] == "synthetic_training_ready"
        assert report["syntheticTypes"] == SYNTHETIC_TYPES
        assert summary["synthetic_training_ready"] is True
        assert summary["synthetic_items"] == len(replay_memory) * len(SYNTHETIC_TYPES)
        assert {"user_question", "user_feedback", "user_interaction", "user_risk"}.issubset(types)
        assert "high" in risks
        assert all(item["simulated_user_input"] for item in dataset)
        assert all(item["simulated_feedback"] for item in dataset)
        assert all(item["simulated_interaction"] for item in dataset)
        assert all(item["training_objective"] for item in dataset)
        assert all(0 < item["training_weight"] <= 1 for item in dataset)

        root = Path(tmp) / "synthetic_training"
        assert (root / "SYNTHETIC_FEEDBACK_TRAINING_REPORT.json").exists()
        assert (root / "synthetic_training_dataset.json").exists()
        assert (root / "synthetic_training_feed.json").exists()
        assert (root / "synthetic_training_summary.json").exists()

    print("synthetic_feedback_training_smoke_test passed")


if __name__ == "__main__":
    main()
