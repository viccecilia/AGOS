from __future__ import annotations

import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.runtime_engine import RuntimeEngine
from services.runtime_persistence import RuntimePersistence


def main() -> None:
    root = Path("runtime/test_runtime_memory")
    if root.exists():
        shutil.rmtree(root)

    engine = RuntimeEngine(RuntimePersistence(root / "state", root / "logs"))
    engine.initialize(workspace="jag_app_growth", industry_pack="Travel Pack", cycle="CYCLE-0043")
    state = engine.start()

    while state["current_stage"] != "Human Review":
        state = engine.advance()
    state = engine.advance()
    assert state["status"] == "needs_human_review"
    review_id = state["review_queue"][0]["review_id"]
    state = engine.approve_review(review_id)
    assert state["current_stage"] == "Learn"
    state = engine.advance()
    assert state["current_stage"] == "Deposit"
    assert state["learning_deposits"]

    libraries = {item["library"] for item in state["learning_deposits"]}
    assert {
        "Question Inbox",
        "Pain Point Library",
        "Answer Branch Library",
        "Learning Events",
        "Workspace Memory",
        "Industry Pack Memory",
        "Strategy Memory",
    }.issubset(libraries)

    shutil.rmtree(root)
    print("runtime memory deposit smoke test passed")


if __name__ == "__main__":
    main()
