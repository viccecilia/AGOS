from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.runtime_engine import RuntimeEngine
from services.runtime_persistence import RuntimePersistence
from services.runtime_ui_bridge import RuntimeUIBridge


HTML_PATH = PROJECT_ROOT / "docs" / "project_control_center.html"


def main() -> None:
    root = Path("runtime/test_runtime_bridge")
    if root.exists():
        shutil.rmtree(root)

    persistence = RuntimePersistence(root / "state", root / "logs")
    bridge = RuntimeUIBridge(RuntimeEngine(persistence=persistence))
    state = bridge.engine.initialize(workspace="jag_app_growth", industry_pack="Travel Pack", cycle="CYCLE-0044")
    assert state["status"] == "idle"

    payload = bridge.handle_action("start")
    assert payload["status"] == "running"
    assert payload["current_stage"] == "Collect"

    ui_state = bridge.export_ui_state()
    assert ui_state["runtimeStatus"] == "RUNNING"
    assert ui_state["current_runtime_stage"] == "Collect"
    assert ui_state["warRoomFeed"]
    assert (root / "state" / "ui_state.json").exists()

    saved = json.loads((root / "state" / "ui_state.json").read_text(encoding="utf-8"))
    assert saved["systemControl"]["currentCycle"] == "CYCLE-0044"
    docs_mirror = PROJECT_ROOT / "docs" / "runtime" / "runtime_state" / "ui_state.json"
    assert docs_mirror.exists(), "docs runtime mirror is required for the current static docs server"
    mirror = json.loads(docs_mirror.read_text(encoding="utf-8"))
    assert mirror["current_runtime_stage"] == "Collect"

    html = HTML_PATH.read_text(encoding="utf-8")
    assert "fetchRuntimeBridgeState" in html
    assert "runtime/runtime_state/ui_state.json" in html
    assert re.search(r"setInterval\(fetchRuntimeBridgeState,\s*2500\)", html)

    shutil.rmtree(root)
    print("runtime ui bridge smoke test passed")


if __name__ == "__main__":
    main()
