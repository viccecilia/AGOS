from __future__ import annotations

import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.personality_memory_deposit import PersonalityMemoryDeposit


def main() -> None:
    root = Path("runtime/test_personality_memory")
    reviews = Path("runtime/test_personality_reviews")
    for path in [root, reviews]:
        if path.exists():
            shutil.rmtree(path)

    deposit = PersonalityMemoryDeposit(root, reviews)
    approved = deposit.deposit(
        {
            "category": "approved_personality",
            "workspace": "JAG-LAB",
            "platform": "reddit",
            "market": "Japan",
            "tone": "trusted_guide",
            "style": ["真实", "可信", "不营销"],
            "reason": "Best guide-like style.",
        }
    )
    rejected = deposit.deposit(
        {
            "category": "rejected_personality",
            "workspace": "JAG-LAB",
            "platform": "tiktok",
            "market": "Japan",
            "tone": "aggressive_hook",
            "style": ["标题党", "过度情绪"],
            "reason": "Creates personality drift.",
        }
    )
    status = deposit.status()
    assert approved["tone"] == "trusted_guide"
    assert rejected["tone"] == "aggressive_hook"
    assert status["bestPersonality"]["tone"] == "trusted_guide"
    assert status["failedPersonality"]["tone"] == "aggressive_hook"
    assert status["personalityDrift"] == "needs_human_review"
    assert (reviews / "PERSONALITY_REVIEW_REPORT.json").exists()

    shutil.rmtree(root)
    shutil.rmtree(reviews)
    print("personality_memory_deposit_smoke_test passed")


if __name__ == "__main__":
    main()
