from __future__ import annotations

import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.personality_engine import PersonalityEngine


def main() -> None:
    root = Path("runtime/test_personality_engine")
    if root.exists():
        shutil.rmtree(root)

    engine = PersonalityEngine(root)
    state = engine.build_context("JAG-LAB", "reddit", "Japan", "trusted_guide")
    assert "真实" in state["workspacePersonality"]["personality"]
    assert "不营销" in state["workspacePersonality"]["personality"]
    assert state["platformPersonality"]["platform"] == "reddit"
    assert "深度" in state["platformPersonality"]["style"]
    assert state["marketPersonality"]["market"] == "Japan"
    assert state["tonePersonality"]["tone"] == "trusted_guide"
    assert (root / "personality_state.json").exists()

    shutil.rmtree(root)
    print("personality_engine_smoke_test passed")


if __name__ == "__main__":
    main()
