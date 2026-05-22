from __future__ import annotations

import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.human_feedback_learning import HumanFeedbackLearning
from services.runtime_correction_engine import RuntimeCorrectionEngine


def main() -> None:
    root = Path("runtime/test_runtime_correction_panel")
    if root.exists():
        shutil.rmtree(root)

    correction_engine = RuntimeCorrectionEngine(root / "state")
    learner = HumanFeedbackLearning(root / "review_sessions")
    correction = correction_engine.reject(
        {
            "target_type": "platform_style",
            "target_id": "STYLE-001",
            "reason": "TikTok emotional spam pattern is too aggressive.",
            "rejected_learning": {"platform": "TikTok", "bad_pattern": "panic hook"},
        }
    )
    decision = learner.record_correction(
        correction,
        {
            "workspace": "JAG-LAB",
            "industry_pack": "Travel Pack / Lab",
            "affected_runtime_stage": "Generate",
            "correction_type": "错误平台风格",
            "correction_reason": "TikTok emotional spam pattern is too aggressive.",
        },
    )

    assert correction["status"] == "rejected"
    assert decision["correction_type"] == "错误平台风格"
    assert (root / "review_sessions" / "correction_decisions.json").exists()
    assert (root / "review_sessions" / "human_preference_memory.json").exists()
    assert learner.summary()["topCorrectedMistakes"][0]["target_type"] == "错误平台风格"

    shutil.rmtree(root)
    print("runtime_correction_panel_smoke_test passed")


if __name__ == "__main__":
    main()
