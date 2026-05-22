from __future__ import annotations

import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.human_feedback_learning import HumanFeedbackLearning


def main() -> None:
    root = Path("runtime/test_human_feedback_learning")
    if root.exists():
        shutil.rmtree(root)

    learner = HumanFeedbackLearning(root)
    learner.record_review_decision(
        {
            "review_id": "REV-APPROVE",
            "workspace": "JAG-LAB",
            "cycle": "CYCLE-TEST",
            "target_type": "Reply",
            "content": {"reply_text": "Helpful route-first answer."},
        },
        "approve",
    )
    learner.record_review_decision(
        {
            "review_id": "REV-REJECT",
            "workspace": "JAG-LAB",
            "cycle": "CYCLE-TEST",
            "target_type": "Strategy",
            "content": {"strategy": "Buy now urgency."},
        },
        "reject",
        {"reason": "Too sales-heavy for travel help."},
    )
    learner.record_review_decision(
        {
            "review_id": "REV-MODIFY",
            "workspace": "JAG-LAB",
            "cycle": "CYCLE-TEST",
            "target_type": "Content",
            "content": {"text": "Follow for more."},
        },
        "modify",
        {"human_modified_version": "Offer one practical tip first."},
    )

    summary = learner.summary()
    memory = summary["humanPreferenceMemory"]
    assert memory["approved"]["Reply"] == 1
    assert memory["rejected"]["Strategy"] == 1
    assert memory["modified"]["Content"] == 1
    assert summary["humanDecisionsToday"] >= 3
    assert (root / "human_modified_outputs.json").exists()

    shutil.rmtree(root)
    print("human_feedback_learning_smoke_test passed")


if __name__ == "__main__":
    main()
