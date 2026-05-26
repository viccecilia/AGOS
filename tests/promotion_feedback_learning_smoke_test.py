from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.promotion_feedback_learning import PromotionFeedbackLearning
from services.promotion_review_center import PromotionReviewCenter


def main() -> None:
    PromotionReviewCenter().build()
    report = PromotionFeedbackLearning().learn()
    events = report["promotionFeedbackEvents"]
    memory = report["promotionLearningMemory"]
    best = report["bestPromotionPatterns"]
    failed = report["failedPromotionPatterns"]
    summary = report["promotionFeedbackSummary"]

    assert report["status"] == "promotion_feedback_learning_ready"
    assert summary["promotion_feedback_learning_ready"] is True
    assert len(summary["feedback_types_observed"]) >= 5
    assert summary["feedback_event_count"] == len(events)
    assert best, "best patterns expected"
    assert failed, "failed patterns expected"
    assert summary["best_pattern_count"] == len(best)
    assert summary["failed_pattern_count"] == len(failed)
    assert summary["next_recommendation"]
    assert summary["sample_data_only"] is True
    assert summary["real_business_result"] is False
    assert summary["auto_next_action_allowed"] is False
    assert summary["unsafe_in_best_patterns"] is False

    observed = set(summary["feedback_types_observed"])
    assert {"posted_manually", "liked", "replied", "saved", "shared"} <= observed
    assert "rejected_by_human" in observed
    assert "modified_by_human" in observed
    assert "unsafe_flagged" in observed

    rejected_events = [event for event in events if event["feedback_type"] == "rejected_by_human"]
    unsafe_events = [event for event in events if event["feedback_type"] == "unsafe_flagged"]
    assert rejected_events
    assert unsafe_events
    assert any(item["failed_feedback"] > 0 for item in failed), "failed learning must include rejected/unsafe/ignored patterns"
    assert any(item["unsafe_feedback"] > 0 for item in failed), "unsafe flags must enter failed learning"
    assert not any(item["value"] == "unsafe_flagged" for item in best), "unsafe feedback cannot become a best strategy"

    for dimension in [
        "problem_type",
        "pain_point",
        "platform",
        "market",
        "answer_style",
        "cta_style",
        "content_format",
        "risk_pattern",
    ]:
        assert dimension in memory
        assert isinstance(memory[dimension], list)

    for output_name in [
        "promotion_feedback_events.json",
        "promotion_learning_memory.json",
        "best_promotion_patterns.json",
        "failed_promotion_patterns.json",
        "promotion_feedback_summary.json",
    ]:
        path = PROJECT_ROOT / "runtime" / "promotion_feedback_learning" / output_name
        assert path.exists(), f"missing output: {output_name}"
        json.loads(path.read_text(encoding="utf-8"))

    print("promotion_feedback_learning_smoke_test passed")


if __name__ == "__main__":
    main()
