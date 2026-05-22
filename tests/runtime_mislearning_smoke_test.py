from __future__ import annotations

import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.runtime_correction_engine import RuntimeCorrectionEngine


def main() -> None:
    root = Path("runtime/test_runtime_mislearning")
    if root.exists():
        shutil.rmtree(root)

    engine = RuntimeCorrectionEngine(root)
    alerts = engine.detect_mislearning(
        {
            "reply_text": "Buy now, this shocking Japan travel trick is a limited offer.",
            "hook": "你绝对想不到",
            "strategy": "Philips air fryer angle in JAG workspace",
        }
    )
    statuses = {item["status"] for item in alerts}
    issues = {item["issue"] for item in alerts}
    assert "needs_human_review" in statuses
    assert "needs_code_check" in statuses
    assert "过度营销风险" in issues
    rejected = engine.reject({"target_id": "bad_learning", "reason": "wrong platform style"})
    assert rejected["status"] == "rejected"
    assert engine.list()

    shutil.rmtree(root)
    print("runtime mislearning smoke test passed")


if __name__ == "__main__":
    main()
