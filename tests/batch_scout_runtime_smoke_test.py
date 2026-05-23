from __future__ import annotations

import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.batch_scout_runtime import BatchScoutRuntime, MAX_BATCH_SIZE, MIN_BATCH_SIZE


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "batch_runtime"
        runtime = BatchScoutRuntime(root)
        questions = BatchScoutRuntime.generate_sample_questions(75)
        report = runtime.run(questions)

        assert report["report_id"] == "BATCH_SCOUT_RUNTIME_REPORT"
        assert report["status"] == "batch_processed"
        assert report["scope"] == "local_batch_scout_runtime"
        assert report["batchLimits"]["min_questions"] == MIN_BATCH_SIZE
        assert report["batchLimits"]["max_questions"] == MAX_BATCH_SIZE

        summary = report["batchScoutSummary"]
        assert summary["questions_processed"] == 75
        assert summary["scout_completed"] == 75
        assert summary["analyze_completed"] == 75
        assert summary["classify_completed"] == 75
        assert summary["priority_ranked"] == 75
        assert summary["batch_runtime_ready"] is True
        assert summary["top_priority_score"] >= 90

        ranking = report["batchPriorityRanking"]
        assert len(ranking) == 75
        assert ranking[0]["rank"] == 1
        assert ranking[-1]["rank"] == 75
        assert ranking[0]["priority_score"] >= ranking[-1]["priority_score"]

        for item in report["batchAnalysis"]:
            assert item["scout_status"] == "scouted"
            assert item["analysis_status"] == "analyzed"
            assert item["classification_status"] == "classified"
            assert item["priority_score"] >= 0
            assert item["priority_band"] in {"critical", "high", "medium", "watch"}
            assert item["recommended_runtime_action"]

        assert report["batchScoutFeed"], "batch scout feed is required"
        assert (root / "BATCH_SCOUT_RUNTIME_REPORT.json").exists()
        assert (root / "batch_questions.json").exists()
        assert (root / "batch_analysis.json").exists()
        assert (root / "batch_priority_ranking.json").exists()
        assert (root / "batch_scout_feed.json").exists()

        for invalid_count in (49, 501):
            try:
                BatchScoutRuntime.generate_sample_questions(invalid_count)
            except ValueError:
                pass
            else:
                raise AssertionError(f"invalid batch size {invalid_count} was accepted")

    print("batch scout runtime smoke test passed")


if __name__ == "__main__":
    main()
