from __future__ import annotations

import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.runtime_replay_training import REPLAY_SOURCE_TYPES, RuntimeReplayTraining


def main() -> None:
    sources = {
        "questions": [
            {
                "question_id": "Q-001",
                "detected_topic": "Tokyo transport anxiety",
                "why_important": "Repeated anxiety about first-time subway use.",
                "priority_band": "critical",
            }
        ],
        "replies": [
            {
                "reply_attempt_id": "RA-001",
                "platform": "Reddit",
                "reply_text": "Use station names plus exits, not only line colors.",
                "status": "approved",
            }
        ],
        "feedback": [
            {
                "feedback_id": "FB-001",
                "reply_attempt_id": "RA-001",
                "liked": True,
                "replied": True,
                "saved": True,
                "feedback_type": "high_engagement",
            }
        ],
        "failures": [
            {
                "failure_id": "FAIL-001",
                "failure_type": "over_marketing",
                "failure_reason": "Reply sounded too promotional for Reddit.",
                "severity": "high",
            }
        ],
        "patterns": [
            {
                "pattern_id": "PAT-001",
                "pattern_type": "high_value",
                "cluster_name": "Airport transfer confusion",
                "result_pattern": "Decision pressure decreases when the reply compares options.",
            }
        ],
    }
    with tempfile.TemporaryDirectory() as tmp:
        replay = RuntimeReplayTraining(Path(tmp) / "replay_training").replay(sources)
        summary = replay["replayTrainingSummary"]
        source_types = {item["source_type"] for item in replay["replayMemory"]}
        results = {item["replay_result"] for item in replay["replayMemory"]}

        assert replay["status"] == "runtime_replay_trained"
        assert replay["replaySourceTypes"] == REPLAY_SOURCE_TYPES
        assert summary["replay_training_ready"] is True
        assert summary["replay_items"] >= 5
        assert {"historical_question", "historical_reply", "historical_feedback", "historical_failure"}.issubset(source_types)
        assert "question_priority_retrained" in results
        assert "reply_strategy_retrained" in results
        assert "engagement_pattern_reinforced" in results
        assert "risk_pattern_reinforced" in results
        assert all(item["updated_intelligence"] for item in replay["replayMemory"])
        assert all(0 < item["training_weight"] <= 1 for item in replay["replayMemory"])

        root = Path(tmp) / "replay_training"
        assert (root / "RUNTIME_REPLAY_TRAINING_REPORT.json").exists()
        assert (root / "replay_training_items.json").exists()
        assert (root / "replay_memory.json").exists()
        assert (root / "runtime_replay_feed.json").exists()
        assert (root / "replay_training_summary.json").exists()

    print("runtime_replay_training_smoke_test passed")


if __name__ == "__main__":
    main()
