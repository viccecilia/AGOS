from __future__ import annotations

import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.runtime_drift_monitor import RuntimeDriftMonitor


def main() -> None:
    root = Path("runtime/test_runtime_drift_monitor")
    if root.exists():
        shutil.rmtree(root)

    monitor = RuntimeDriftMonitor(root)
    events = monitor.detect(
        {
            "reply_text": "Buy now, click here, this shocking secret trick helps every traveler.",
            "platform_style": "Reddit short hook",
            "workspace_context": "Philips air fryer should not appear in JAG-LAB.",
            "learning": "Everything is high value and always reply.",
        }
    )
    issues = {item["issue"] for item in events}
    assert "spam tendency" in issues
    assert "platform personality drift" in issues
    assert "workspace pollution" in issues
    assert "clickbait tendency" in issues
    assert monitor.summary()["runtimeDriftStatus"] == "needs_human_review"
    assert monitor.summary()["needsCodeCheck"] is True

    shutil.rmtree(root)
    print("runtime_drift_monitor_smoke_test passed")


if __name__ == "__main__":
    main()
