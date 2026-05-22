from __future__ import annotations

import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.human_feedback_learning import HumanFeedbackLearning
from services.human_review_runtime import HumanReviewRuntime


def main() -> None:
    root = Path("runtime/test_runtime_review_queue")
    if root.exists():
        shutil.rmtree(root)

    review = HumanReviewRuntime(root / "state")
    learner = HumanFeedbackLearning(root / "review_sessions")
    item = review.request_review(
        {
            "workspace": "JAG-LAB",
            "cycle": "JAG-LAB-CYCLE-REVIEW",
            "target_type": "Reply",
            "source_platform": "Reddit",
            "country": "Japan",
            "language": "en",
            "pain_point": "Tokyo transport anxiety",
            "ai_reason": "This reply may teach AGOS a reusable first-trip rescue pattern.",
            "risk_level": "medium",
            "content": {"reply_text": "Use station names and one backup route."},
        }
    )
    assert review.pending()[0]["review_id"] == item["review_id"]
    assert review.pending()[0]["ai_reason"]

    approved = review.approve(item["review_id"])
    learner.record_review_decision(approved, "approve")
    assert approved["status"] == "approved"

    rejected_item = review.request_review({"target_type": "Strategy", "content": {"strategy": "limited offer hook"}})
    rejected = review.reject(rejected_item["review_id"], "Too promotional for Reddit.")
    learner.record_review_decision(rejected, "reject", {"reason": "Too promotional for Reddit."})
    assert rejected["status"] == "rejected"
    assert rejected["reason"] == "Too promotional for Reddit."

    modified_item = review.request_review({"target_type": "Content", "content": {"text": "Follow for more tips."}})
    modified = review.modify(
        modified_item["review_id"],
        {"human_modified_version": "Give one useful route tip without asking for follows."},
    )
    learner.record_review_decision(
        modified,
        "modify",
        {"human_modified_version": "Give one useful route tip without asking for follows."},
    )
    assert modified["status"] == "modified"
    assert modified["modified_content"]["human_modified_version"]

    summary = learner.summary()
    assert summary["humanPreferenceMemory"]["approved"]["Reply"] == 1
    assert summary["humanPreferenceMemory"]["rejected"]["Strategy"] == 1
    assert summary["humanPreferenceMemory"]["modified"]["Content"] == 1

    shutil.rmtree(root)
    print("runtime_review_queue_smoke_test passed")


if __name__ == "__main__":
    main()
