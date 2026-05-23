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
from services.runtime_pattern_learning import PATTERN_TYPES, RuntimePatternLearning


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        scout = BatchScoutRuntime(base / "batch_runtime").run(
            BatchScoutRuntime.generate_sample_questions(100)
        )
        clusters = BatchTopicClustering(base / "batch_clusters").cluster(scout["batchAnalysis"])
        review = BatchHumanReview(base / "batch_reviews").review(clusters["batchTrendClusters"])
        learned = RuntimePatternLearning(base / "pattern_memory").learn(review["batchReviewQueue"])

        summary = learned["patternLearningSummary"]
        pattern_types = {item["pattern_type"] for item in learned["patternMemory"]}

        assert learned["status"] == "runtime_patterns_learned"
        assert learned["patternTypes"] == PATTERN_TYPES
        assert summary["patterns_learned"] == review["batchHumanReviewSummary"]["review_items"]
        assert summary["pattern_memory_ready"] is True
        assert "high_value" in pattern_types
        assert "high_risk" in pattern_types
        assert "high_engagement" in pattern_types or "high_conversion" in pattern_types
        assert all(item["question_combination"] for item in learned["patternMemory"])
        assert all(item["result_pattern"] for item in learned["patternMemory"])
        assert all(item["recommended_next_action"] for item in learned["patternMemory"])
        assert all(0 < item["learning_weight"] <= 1 for item in learned["patternMemory"])

        assert (base / "pattern_memory" / "RUNTIME_PATTERN_LEARNING_REPORT.json").exists()
        assert (base / "pattern_memory" / "pattern_memory.json").exists()
        assert (base / "pattern_memory" / "runtime_pattern_feed.json").exists()
        assert (base / "pattern_memory" / "pattern_learning_summary.json").exists()

    print("runtime_pattern_learning_smoke_test passed")


if __name__ == "__main__":
    main()
