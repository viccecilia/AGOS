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
    root = Path("runtime/test_runtime_engine")
    if root.exists():
        shutil.rmtree(root)

    engine = RuntimeEngine(RuntimePersistence(root / "state", root / "logs"))
    state = engine.initialize(workspace="jag_app_growth", industry_pack="Travel Pack", cycle="CYCLE-0042")
    assert state["status"] == "idle"
    assert state["current_stage"] == "Scout"

    state = engine.start()
    assert state["status"] == "running"
    assert state["runtime_queue"]

    state = engine.advance()
    assert state["current_stage"] == "Collect"
    assert state["pipeline"][0]["status"] == "done"

    state = engine.pause()
    assert state["status"] == "paused"

    state = engine.stop()
    assert state["status"] == "stopped"

    saved = engine.persistence.load_state()
    assert saved["cycle"] == "CYCLE-0042"
    assert saved["current_stage"] == "Collect"
    assert engine.persistence.load_events()

    shutil.rmtree(root)
    print("runtime engine smoke test passed")


if __name__ == "__main__":
    main()
