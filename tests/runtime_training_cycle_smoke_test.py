from __future__ import annotations

import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.runtime_engine import RuntimeEngine
from services.runtime_persistence import RuntimePersistence
from services.runtime_review_session import RuntimeReviewSession


def main() -> None:
    root = Path("runtime/test_runtime_training_cycle")
    if root.exists():
        shutil.rmtree(root)

    engine = RuntimeEngine(
        RuntimePersistence(root / "state", root / "logs"),
        review_session=RuntimeReviewSession(root / "reviews"),
    )
    state = engine.run_training_cycle()

    assert state["workspace"] == "JAG-LAB"
    assert state["current_stage"] == "Deposit"
    assert [item for item in state["pipeline"] if item["status"] == "current"][0]["id"] == "Deposit"
    stages = {item["stage"] for item in state["training_explanations"]}
    assert {"Scout", "Analyze", "Learn", "Deposit"}.issubset(stages)
    assert state["opportunity_score"]["verdict"] in {"high_value", "medium_value", "low_value"}
    assert state["runtime_intelligence"]["best_answer"]
    assert state["runtime_review_report"]
    assert engine.persistence.load_events()

    shutil.rmtree(root)
    print("runtime training cycle smoke test passed")


if __name__ == "__main__":
    main()
