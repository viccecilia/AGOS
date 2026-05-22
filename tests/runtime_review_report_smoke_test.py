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
    root = Path("runtime/test_runtime_review_report")
    if root.exists():
        shutil.rmtree(root)

    reviews = root / "reviews"
    engine = RuntimeEngine(
        RuntimePersistence(root / "state", root / "logs"),
        review_session=RuntimeReviewSession(reviews),
    )
    state = engine.run_training_cycle()
    report = state["runtime_review_report"]

    assert report["workspace"] == "JAG-LAB"
    assert "learned" in report
    assert "mislearned" in report
    assert "effective" in report
    assert "ineffective" in report
    assert reviews.exists()

    shutil.rmtree(root)
    print("runtime review report smoke test passed")


if __name__ == "__main__":
    main()
