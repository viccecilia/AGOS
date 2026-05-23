from __future__ import annotations

import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.batch_human_review import BatchHumanReview
from services.batch_scout_runtime import BatchScoutRuntime
from services.batch_topic_clustering import BatchTopicClustering
from services.intelligence_acceleration_gate import IntelligenceAccelerationGate
from services.runtime_pattern_learning import RuntimePatternLearning
from services.runtime_replay_training import RuntimeReplayTraining
from services.synthetic_feedback_training import SyntheticFeedbackTraining


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        batch_scout = BatchScoutRuntime(base / "batch_runtime").run(
            BatchScoutRuntime.generate_sample_questions(100)
        )
        batch_clusters = BatchTopicClustering(base / "batch_clusters").cluster(batch_scout["batchAnalysis"])
        batch_review = BatchHumanReview(base / "batch_reviews").review(batch_clusters["batchTrendClusters"])
        pattern_learning = RuntimePatternLearning(base / "pattern_memory").learn(batch_review["batchReviewQueue"])
        replay_training = RuntimeReplayTraining(base / "replay_training").replay(
            {
                "questions": batch_scout["batchPriorityRanking"][:4],
                "reviews": batch_review["batchReviewQueue"][:4],
                "patterns": pattern_learning["patternMemory"][:4],
                "replies": [
                    {"reply_attempt_id": "RA-001", "platform": "Reddit", "reply_text": "Use station exits.", "status": "approved"}
                ],
                "feedback": [
                    {"feedback_id": "FB-001", "reply_attempt_id": "RA-001", "liked": True, "replied": True, "feedback_type": "high_engagement"}
                ],
                "failures": [
                    {"failure_id": "FAIL-001", "failure_type": "over_marketing", "failure_reason": "Too promotional.", "severity": "high"}
                ],
            }
        )
        synthetic_training = SyntheticFeedbackTraining(base / "synthetic_training").generate(replay_training["replayMemory"])
        gate = IntelligenceAccelerationGate(base / "intelligence_acceleration_gate").evaluate(
            {
                "batch_scout": batch_scout,
                "batch_clusters": batch_clusters,
                "batch_review": batch_review,
                "pattern_learning": pattern_learning,
                "replay_training": replay_training,
                "synthetic_training": synthetic_training,
            }
        )

        review = gate["runtimeIntelligenceEvolutionReview"]
        assert gate["status"] == "passed"
        assert gate["batchIntelligenceAccelerationReady"] is True
        assert len(gate["gateChecks"]) == 6
        assert all(item["status"] == "passed" for item in gate["gateChecks"])
        assert review["gate_status"] == "passed"
        assert review["readiness_to_next_stage"] is True
        assert review["next_stage"] == "Controlled Real External Interaction Stage"
        assert review["questions_processed"] >= 50
        assert review["clusters_created"] >= 1
        assert review["human_review_items"] >= 1
        assert review["patterns_learned"] >= 1
        assert review["replay_items"] >= 1
        assert review["synthetic_items"] >= 1

        root = base / "intelligence_acceleration_gate"
        assert (root / "INTELLIGENCE_ACCELERATION_REPORT.json").exists()
        assert (root / "RUNTIME_INTELLIGENCE_EVOLUTION_REVIEW.json").exists()
        assert (root / "intelligence_acceleration_checks.json").exists()
        assert (root / "intelligence_acceleration_feed.json").exists()

    print("intelligence_acceleration_gate_smoke_test passed")


if __name__ == "__main__":
    main()
